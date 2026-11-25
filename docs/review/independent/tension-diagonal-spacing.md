# Independent assessment

## What the evidence shows

- One check is outside target: `newbeam-tension`, `diagonal_spacing`, Response's stage 12 (cracking) against r2c's stage 11. Difference 100 %, 20 × target ("The instances").
- Up to control value 0.064 the two curves agree to about 0.02 load units: Response stage 11 is (0.064, 274.54), r2c stage 11 is (0.064, 274.53) ("The two responses").
- At 0.065 they part. Response stage 12 is (0.065, 276.2), still rising, and falls at stage 13 (0.066, 235.77). r2c stage 12 is (0.065, 239.09), already fallen. r2c falls one stage earlier.
- After the fall they agree again: at 0.066, 235.77 against 235.09. Peak, rising branch and post-peak differ by 0.21 %, 0.48 % and 0.22 %.
- Response's stage 12 chart shows 600 from depth 300 to 285.17 and 0 below. r2c's stage 11 chart is 0 at every depth (`viewlines.py ... diagonal_spacing`).
- Response's crack widths at stage 12 are 0.0002 and 0.0001 at the top two points, 0 elsewhere. r2c's are all 0 (`viewlines.py ... crack_widths`).
- Response's chart has 35 depth points, with extra points between 300 and 274.35. r2c's has 23.
- "r2c in Response's own state": 0.0 % ("The instances").
- The measure reads the features as "cracking, fall, peak" for Response and "fall, cracking, peak" for r2c.

## The reason

- **measured**: r2c has no stage like Response's stage 12. Response records a stage where the top 15 mm has just cracked and the load is still rising (276.2). r2c goes from wholly uncracked (stage 11, 274.53) straight to the fallen state (stage 12, 239.09). The check pairs Response's partly cracked stage with r2c's last uncracked one, so 600 is compared with 0: 100 %.
- **measured**: r2c's spacing rule is not the cause in this state. The "r2c in Response's own state" diagnostic gives 0.0 %: fed Response's strains, r2c draws Response's chart.
- **inferred**: the difference therefore lies in which states are reached near 0.065: the step control, or which of two solutions the solver finds at the same control value (partly cracked at high load, or cracked at low load). Nothing in the file tests either.
- **read**: nothing. The file gives no rule of the binary, no address and no decompiled routine.

## What the evidence does not establish

- Why r2c falls a stage early. No trace is in the file. A `tools/rtrace.py` / `tools/tries.py` trace of the tries around stages 11 to 13, both programs, would best settle it.
- Whether the control values are the same. Both print 0.065, at three decimals, so r2c's stage 12 may be at a slightly larger strain than Response's. Unrounded control values would settle it.
- What r2c's own cracked stage 12 shows. Its chart is not given, so whether r2c agrees with Response once cracked (Response stage 13 against r2c stage 12) is unknown. `viewlines.py` at those stages would show it.
- Whether the extra depth points in Response's chart (35 against 23) mark a layering rule r2c lacks, or one r2c applies only once cracked. Not tested.
- Whether the check should be assessed at all. Response's stage 11 and 13 views are not given, so the instability test cannot be checked here. The curve suggests a step (assessed), not a spike.
- The file lists one check outside target, yet the feature order differs between the programs. Shape is a Must. Whether shape is outside and held in another group, or passes by some rule not stated, the file does not say. This needs an answer.

## Against the targets

- `diagonal_spacing` is in the **Could** tier (views related to cracking, every case). Target 5 %; the difference is 100 %, 20 × target, the largest possible by this measure. One check, one case, one stage.
- `crack_widths` at the same stage differs by 0.0002, within two units of the last printed digit, so it is not a miss.
- Peak (0.21 %), rising branch (0.48 %) and post-peak (0.22 %) are inside the 5 % targets.
- Shape (Must): the file's own reading of the features differs in order. On the evidence given, I cannot confirm it is inside target.

## On the developer's reason

1. **Supported, as far as it goes.** The 0.0 % of "r2c in Response's own state" and the two `viewlines.py` charts (600 over the top 15 mm against 0 everywhere) bear out each fact stated. The mark **measured** is right for those facts. The closing phrase, "it is the stage compared", is weaker than it sounds: the pairing is not at fault. r2c has no partly cracked stage to compare (its stage 12 has already fallen to 239.09), so the miss is a difference in the response the clone computes, not only in how the measure pairs stages. The part also gives no cause for that difference.
2. **Not decided, but consistent.** The curves show what it describes: r2c's last uncracked stage (0.064, 274.53) is paired with Response's first cracked one (0.065, 276.2), and the features read in a different order for the two programs. That the two entries share one cause is plausible; nothing in my file tests it, and the shape entry itself is not in my file. The mark **inferred** is right, and the developer says plainly it was not tested.

The developer's account leaves out two things my file shows: r2c falls one stage earlier than Response, and the feature order (a Must check) differs. Neither contradicts the account.

Verdict: supports
Suggestion: take up again - the measured part holds but stops short of a cause, and the same early fall changes the order of the curve's features, which is a Must, so one trace of the tries around stages 11 to 13 is worth its cost.
