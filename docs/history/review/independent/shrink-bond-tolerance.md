# Independent assessment

## What the evidence shows

- One check is outside target: `transverse_average_bond`, case `newbeam-shrink-m`, Response's last stage 46 against r2c's stage 46: 6.1 %, 1.2 × target ("The instances").
- The control curves agree: peak +0.00 %, rising branch 0.00 %, post-peak 0.01 %, same features ("The two responses").
- The gap is at the top of the chart. At depths 255, 240, 225 and 210 Response shows 0.0641, 0.0669, 0.0714 and 0.0450; r2c shows 0, 0, 0 and 0.0021. Lower down they differ less: 1.0567 against 1.0126 at 195 (`viewlines.py ... transverse_average_bond --raw`).
- Response's stirrup stress is −59.686 at five neighbouring nodes (248.7 to 214.3) and −59.06 to −59.09 at the other nodes of that zone. r2c's is −59.062 at every one. There is also a difference of −1.178 at 175.4 (`viewlines.py ... stirrup_stress`).
- `bond.py --stages 46`: largest difference 0.0 % (record 1.0195, rule 1.0196).
- "r2c in Response's own state": 6.1 %, unchanged ("The instances").

## The reason

- **measured**: the miss is Response's 0.064 to 0.071 MPa between 255 and 225 where r2c has nothing (`viewlines.py --raw`; 0.0641 of 1.0567 is 6.1 %).
- **measured**: at those depths Response's stirrup stress has a block 0.624 MPa away from its neighbours, and r2c's is uniform (`viewlines.py stirrup_stress`). The two line up in depth.
- **measured**: putting r2c in Response's strain state changes nothing (6.1 %). So the gap does not come from a different longitudinal or shear state. It comes from something worked out at each node.
- **measured, with a caveat**: `bond.py` gives 0.0 %. If that tool applies the bond rule to Response's own stirrup stresses, the bond rule is cleared and the stirrup stresses are the cause. The file does not say what the tool does, so that reading is inferred.
- **read**: `004a8b20`. The decompiled routine bears out that the transverse value is found by a loop that stops when a residual falls under a tolerance (a relative part plus a fixed part), with the step changed at the 15th pass and a failure return after 30. It also bears out the form of the offset test (four absolute values summed and compared with a constant). The values of the constants are not in the file, so "10⁻⁶" and the size of the tolerance are unchecked.
- **inferred**: that this tolerance is what leaves five nodes 0.62 MPa off. Nothing in the file tests it.

## What the evidence does not establish

- **Tolerance or rule?** The five nodes are one unbroken block at the top end of the stirrups (non-zero from 253.9), not scatter. A rule that acts differently there is not excluded. Best diagnostic: the binary's exit test evaluated at Response's own transverse strain at those nodes, with a count of the passes each took.
- **Failure route.** The routine can return failure after 30 passes. Whether those nodes converged is not shown. The same trace settles it.
- **Other stages.** Only stage 46 is shown. Whether the block is there at earlier stages, at the same depths, is unknown. The same stirrup listing at the peak and at cracking would show it.
- **The −1.178 MPa at 175.4** is larger than the "up to 0.6" in the rule's description, and is not explained. It sits by the 4.2 % difference at 195, which is inside target.
- **What `bond.py` computes** is missing.

## Against the targets

- `transverse_average_bond` is in the `should` list. The case has no shear increment, so it is a flexure case. The check is in the Should tier.
- Size: 6.1 % against `views_pct` of 5 %, 1.2 × target. The plain gap at depth 225 is larger (0.0714, 6.8 %); the measure is a distance between curves. Either way it is outside. The printed-precision floor (two units of the fourth decimal) does not reach it.
- Stage 46 is the last stage, so the instability test does not apply and the check stays assessed.
- Peak, rising branch, post-peak and shape are inside target.

## On the developer's reason

1. **Supported in part.** The stirrup listing bears out the first sentence: r2c is −59.062 at every node of the zone, and Response is not. "A little from point to point" understates the pattern, though: most of Response's nodes are within 0.025 MPa, and one unbroken block of five (248.7 to 214.3) is 0.624 off. The second sentence, that the bond chart is the difference between neighbouring points, is not shown by the file. No bond rule is given with an address, and what `bond.py` computes is not described. A plain neighbour difference would put the bond at the two edges of the block (near 250 and 211), yet Response's chart is non-zero at 240 and 225 as well, inside the block where the stress is flat. The mark **measured** is right for the stirrup stresses and wrong for how the bond chart is made: that half is inferred, or read without its source in the file.
2. **Does not decide.** The decompiled `004a8b20` shows that a tolerance-stopped loop exists, which makes the claim possible. Nothing shows that it produces 0.62 MPa at just those five nodes, and a block at the top end of the stirrups looks more like something systematic than like stopping scatter. The mark **inferred** is the right one. The statement that testing it "would mean copying that iteration step for step" is not borne out: evaluating the routine's exit test at Response's own transverse strain at those nodes, or tracing the passes each node took, would test it without cloning the loop.

Verdict: does not decide
Suggestion: take up again - the part the explanation depends on (a tolerance, not a missing rule) is untested, the five-node block does not look like stopping scatter, and one diagnostic short of copying the iteration would settle it.
