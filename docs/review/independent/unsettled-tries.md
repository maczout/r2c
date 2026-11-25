# Independent assessment

## What the evidence shows

- **The instances table.** 50 checks on 11 shear cases: 2 shape, 44 Should views, 4 Could views. For every view, "r2c in Response's own state" is inside target (0.0 to 4.9 %). Peak loads agree within 0.3 % on 9 cases (+2.79 % on `newbeam-m2v`, +1.52 % on `newbeam-tstiff6-mv`).
- **Same table, transverse bond.** It is 12 of the 48 views and the two worst (71.5 %, 49.8 %). On six of them the own-state figure is 3.0 to 4.9 %, close to the target.
- **Views at the compared stages.** The bond differences sit in a few layers: `newbeam-nmv-incr` 17 to 27 against 0 to 3 at four depths; `igirder-mv` 3249 against 1630 at two depths; the rest of each chart agrees.
- **`tries.py`, `newbeam-us-mv`.** The two programs agree for 29 tries. At the next (curvature 1.8379, multiplier 0.25) Response refuses after 16 passes with profile error 14.29 %; r2c keeps it at 2.01 %. From there the stage sequences differ (Response 56 stages, r2c 50).
- **`tries.py`, `column-mv`.** 40 tries agree, including stage 36 (the peak): both kept after 16 passes, error 1.35 % (Response) and 0.99 % (r2c), loads 417.81 and 417.74.
- **`startfrom.py`, `column-mv` stage 36.** Started from Response's stage 35, r2c reaches the load within 0.05 % in all four variants, but the shear strain profile differs by 9.1 to 18.4 % and stirrup stress by 14.0 % (1.6 % in Response's state).
- **`startfrom.py`, `newbeam-nmv-incr` stage 36.** Under curvature control the load is within 0.16 %; transverse bond is 71.4 % off (0.5 % in Response's state).
- **`repeat.py`.** Response repeats exactly over 4 captures on three cases.
- **The two responses.** `newbeam-us-mv` and `newbeam-usfile-mv` (peaks 57.851 and 57.824) differ in Response itself: 57 against 53 stages, and the large fall lands at 40.2 against 43.2.
- **Rules claimed.** The record says r2c does not run Response's global solve (`004276a0`, "off") nor its per-pass test of the state code (`00418af0`, "off").

## The reason

I see four things, not one.

1. **Not the section rules.** **measured**: the own-state column, at most 4.9 %. Given Response's state, r2c draws Response's charts. The differences are in the state each program stops in.
2. **Unconverged stages kept at pass 16** (`column-mv` stage 36, 11 checks). **measured**: `tries.py` shows the same try kept by both at 16 passes with errors near 1 %; `startfrom.py` shows r2c ending on a profile 9.1 % away at the same load. The state kept is whatever the sixteenth pass leaves, and r2c's passes leave a different one. **inferred**: the same holds for the views at early falls where the tries still agree (`newbeam-us-mv` stage 12, about 10 %); the trace shown starts at try 21, so this is untested.
3. **Different stage sequences on a flat curve** (peak views of `newbeam-us-mv`, `newbeam-usfile-mv`, `newbeam-m05v`, `newbeam-m2v`, `newbeam-m0neg-mv`, `column-interlock-mv`: r2c's stage number differs, load spread 0.02 to 0.72 %). **measured** for `newbeam-us-mv` only: the divergence at try 29, where r2c's passes converge better than Response's (2.01 against 14.29 %). **inferred** for the other five: no trace is given.
4. **Transverse bond** (12 checks). **measured**: differences confined to a few layers, and after `startfrom.py` on `newbeam-nmv-incr` it is the only view outside. **inferred**: the view switches on a discrete condition in those layers, so a small state difference gives a large one. Six instances also carry 3 to 4.9 % from the rule itself.
5. **Why r2c's passes differ.** **read**: `004276a0` (fixed step factor, no line search, loose tolerance, 50 steps). The decompiled routine bears this out in structure; it also shows a 100-step limit in one mode and a halving of the step factor after 10 steps that the description leaves to a section not in the file; the constants' values and `004267c0` are not shown. **read**: `00418af0`; the decompiled routine bears out the order of the tests, constants not shown. r2c knowingly runs neither. **inferred**: that this is the cause. The record's own figures (8 checks in, 13 out with Response's solve on) are not backed by any output in the file, and suggest it is not the whole of it.
6. **Shape** (2 Must). **inferred**: both programs' curves show both falls at the same stages. The first fall is 2.06 % of the peak in Response and 1.99 % in r2c (2.07 and 1.97 % on `newbeam-usfile-mv`), so a threshold in the measure near 2 % may be what separates them. The measure's rule is not in the file.

## What the evidence does not establish

- **Which of r2c's two departures matters.** Best diagnostic: `startfrom.py` on `column-mv` stage 36 with Response's solve and per-pass test switched on.
- **Stages off the peak with agreeing tries** (`newbeam-us-mv` 12, `newbeam-csa-mv` 30, `newbeam-tstiff6-mv` 30): no diagnostic. `startfrom.py` on each.
- **Five cases of part 3**: no trace. `tries.py` on each.
- **The bond mechanism**: the rule is not in the file. A layer-by-layer listing of its inputs at `newbeam-nmv-incr` stage 36 in both states.
- **Shape**: the feature rule and thresholds of the measure are missing; print the measure's features with their sizes.
- **Whether Response is steady here** (D54): neighbouring stages' views are not given. Response's own sensitivity (us against usfile) suggests some checks may be luck, but that is not shown.
- **Tracer effect**: the `column-mv` trace counts 38 Response stages against 40 captured; unexplained.

## Against the targets

- **Must: 2** (shape, `newbeam-us-mv` and `newbeam-usfile-mv`). The differences read are before the peak, so the exclusion of shear endings does not cover them.
- **Should: 44** views, 5.0 to 71.5 % against 5 % (1.0 to 14.3 × target); 24 are at 2 × or more, 8 within half a point of the target.
- **Could: 4** views, 7.4 to 12.3 % (1.5 to 2.5 ×).
- Peak and rising branch are inside target on all 11 cases; post-peak figures outside target appear in the case headers but are not part of this group.

## On the developer's reason

1. **Supports.** Every view's own-state figure is inside target (0.0 to 4.9 %), and 37 of the 48 views are at stages with a load spread under 1 % of the peak, so "most" is right. The mark *measured* is right. Two reservations: six transverse bond figures are 3.0 to 4.9 %, so for those the rule is not clean; and the 11 views off the flat part include the two worst.
2. **Supports the trace, contradicts the shape.** The 29 agreeing tries and the divergence on `newbeam-us-mv` are in `tries.py`; *measured* is right for that, on that one case. Two things are not as stated. At the first difference Response does not "give up its solve": it refuses the stage after 16 passes at 14.29 % error, where r2c's error is 2.01 %; the unsolved tries come after. And r2c's curve does not have one fall where Response has two: both of r2c's curves show both falls, at the same stages as Response (32.72 to 31.57, and 52.6 to 40.6). The first fall is at stage 12, before the tries diverge, and is 1.99 % of the peak against Response's 2.06 %. So "that is the shape" is not measured; it is *inferred*, and the curves speak against it. `newbeam-usfile-mv`, the other shape check, has no trace and a different reading (fall, cracking, peak).
3. **Does not decide, and contradicts in one point.** The decompiled `00418af0` bears out the order of the pass tests, so *read* is right for the rule. But the evidence file says r2c tests the state code once, after the passes, with the per-pass test "off": the pass rule is not wholly in r2c. The figures for the two approaches (18 in, 14 out) are measurements with no output in my file, which gives different figures for the solve (8 in, 13 out); they should be marked *measured* and shown, or not relied on. The growth rule is not in my file.
4. **Does not decide; the mark *inferred* is right, and the part is candid.** But the evidence already speaks against "nothing but the tries" as worded: on `column-mv` the tries agree for 40, through the peak stage, and 11 checks are outside there. It is the passes inside the same try that end differently, not different tries. My file holds two traces and two start-from runs, not four and three; the landing at the tension stiffening case's peak is not in it. The file counts 11 cases, not ten. On timing, `repeat.py` shows exact repeats on three cases, which does not bear out a dependence on timing; the trace's stage count (38 against 40) is the only hint of it.

Verdict: does not decide
Suggestion: take up again - the two Must shape checks are not explained by the tries (both falls are in r2c's curves, the first just under what looks like a threshold of the measure), so the shape reading should be examined before the Should and Could views are accepted as a named limitation.
