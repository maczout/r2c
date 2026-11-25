# Independent assessment

## What the evidence shows

- One case, `newbeam-vonly`, 15 checks: shape, and 14 views, all at Response's stage 10 against r2c's stage 8 ("The instances").
- Response's stage 10 is the first stage after its fall: shear_gxy 0.116, shear_ex 0.002, load 184.69, down from 189.38 at stage 9. r2c's stage 8 is before r2c's own largest load on that branch: shear_gxy 0.112, shear_ex 0.000, load 184.71 ("The two responses"; `tools/curves.py`).
- r2c also drops there, at its own stage 10: 188.77 to 186.25 (shear_gxy 0.117, shear_ex 0.001). That is 2.52, or 1.16 % of the peak. Response's drop is 4.69, or 2.15 % (same lists; my arithmetic).
- At the compared stages, r2c's charts are zero at every depth, on 33 points. Response's are non-zero only between depths 37.5 and -42.5 (stirrup stress, transverse strain, shear on crack), on 75 points ("The views at the compared stages").
- "r2c in Response's own state" is 0.0 % to 1.2 % on all 14 views ("The instances").
- Peak -0.04 %, rising branch 0.28 %, post-peak 40.98 % ("The two responses").
- The `tools/tries.py` extract covers tries 47 to 57 only, the end of the response.

## The reason

- **measured**: the 14 view checks compare states on opposite sides of the fall. `tools/curves.py` gives Response's stage 10 after its drop and r2c's stage 8 before r2c's drop. The loads are equal by coincidence (184.69 and 184.71) and shear_ex differs by 0.002 of a range of 1.199, so stage 8 is the nearest point "at the same place"; r2c's stage 10 is 0.72 % of peak away in load. The curve folds back in load here, so the pairing lands on the wrong branch.
- **measured**: the 100 % figures are a zero chart against a non-zero one (view listings: r2c all 0; Response up to 3.101 stirrup stress, 0.0017 longitudinal strain). The three smaller figures (24.4 %, 15.8 %, 6.9 %) are views that are non-zero on both sides.
- **measured**: r2c's rules are not shown to be the cause. In Response's own state they give Response's charts within 0.0 % to 1.2 % (table, "r2c in Response's own state").
- **measured**: the shape check fails because r2c's drop at this point is about half Response's (1.16 % against 2.15 % of peak, `tools/curves.py`) and the measure reads no "fall" in r2c.
- **inferred**: the fall is the onset of diagonal cracking in the web band, and r2c's solve lands on a slightly different state after it (shear_ex 0.001 against 0.002, load 0.72 % of peak higher). Nothing in the file tests why.
- **read**: nothing. The file gives no rule of the binary and no address.

## What the evidence does not establish

- Whether the views would be inside target at the matching stage. r2c's stage 10 views are not in the file. Best diagnostic: the same view comparison, Response's stage 10 against r2c's stage 10.
- Why r2c's drop is smaller. The in-state result clears the rules in a given state, not the state the solver reaches or the history carried into it. Best diagnostic: the `tools/tries.py` trace around tries 8 to 12, which the extract omits.
- The measure's threshold for a "fall". It is not given, so I cannot say how far r2c's 1.16 % is from counting. Best diagnostic: the measure's own reading of both drops against its limit.
- Whether layer refinement differs (75 points against 33). r2c may refine only once cracked. Best diagnostic: r2c's stage 10 chart.
- Whether the D54 instability test was applied at stage 10. The file does not say.

## Against the targets

- Shape: Must, outside. It is not a number. The difference is a fall before the peak, so the Won't for shear endings does not cover it.
- Should, 12 views (this is a shear case, so stress-state views are Should): nine at 100 % (20 × the 5 % target), then 24.4 % (4.9 ×), 15.8 % (3.2 ×), 6.9 % (1.4 ×).
- Could, 2 views: both 100 % (20 ×).
- Not in this group but outside on the same case: post-peak 40.98 % against 5 %.

## On the developer's reason

1. **Supports.** `tools/curves.py` gives Response's drop as 2.15 % of the peak and r2c's as 1.16 %, and the measure reads "fall" for Response only. The mark "measured" is right for the two drops. The 2 % limit itself is not in my evidence file; it fits the numbers, but I cannot confirm it, and Response's drop clears it by only 0.15 % of the peak. That the fall is "after cracking" is not labelled in the evidence; the charts (zero before, non-zero in the web band after) are consistent with it.
2. **Supports.** All 14 views are at Response's stage 10, and "r2c in Response's own state" is 0.0 % to 1.2 % on every one, inside 5 %. The curves show the paired r2c stage 8 at the same load (184.71 against 184.69) before r2c's own drop, and r2c's charts there are all zero. The mark "measured" is right. It does not show that the views would be inside at r2c's own stage after its drop; that comparison is not in the evidence.
3. **Does not decide.** The 1.2 % agrees with the 1.16 % I get from the curves. The earlier 1.9 % is not in the evidence, and the trace extract (tries 47 to 57) does not cover the fall, so nothing tests whether the cause is the state after cracking or the stage control. The mark "inferred" is right for the conclusion; the two figures quoted in it are measurements the evidence file does not hold.

Verdict: supports
Suggestion: take up again - the shape miss is a Must whose cause the developer says was not read, and the two diagnostics that would narrow it (the trace around the fall, and the views at r2c's own stage after its drop) have not been run.
