# Independent assessment

## What the evidence shows

- One check is outside: `newbeam-tension`, shape, Must ("The instances"). Response reads "cracking, fall, peak, ends standing still"; r2c "fall, cracking, peak, ends standing still".
- The curves differ materially at one stage only ("The two responses"). At stage 12 (control 0.065) Response is at 276.2 and r2c at 239.09: 37.1 lower, 10.5 % of Response's peak. Stage 11 agrees (274.54 / 274.53), stage 13 agrees (235.77 / 235.09). Response's load falls between stages 12 and 13; r2c's between 11 and 12, one stage earlier.
- Elsewhere the curves are close: peak -0.21 %, rising branch 0.48 %, post-peak 0.22 % (same section).
- `tools/branch.py --stage 11 --points 8`: between r2c's stages 11 and 12, at r2c's own stage-12 control value (6.4645e-05), a state exists with N 275.90 kN and a least unbalanced moment of +0.055 kNm. r2c's kept stage 12 is 239.09 kN.
- Rule `004276a0` ("Rules claimed"): Response's solve has a wide stopping tolerance; pre-cracking states on this section are said to carry 40 to 130 N m of unbalanced moment. The same passage says r2c's stiffness and its step are its own, not the binary's.

## The reason

- **measured**: the miss is a one-stage difference in when the load falls at cracking. Curve listing: stage 12, Response 276.2, r2c 239.09; neighbours agree within 0.7.
- **measured**: at that control value r2c has two states: the high one that `branch.py` follows (275.90 kN, 0.3 below Response's 276.2) and the low one it kept (239.09). So r2c's material rules can give Response's load there; r2c's solve or stage control chose the other state. The unbalanced moment of the high state rises over the last two points (0.0225, 0.055 kNm), so it is at the edge of balance.
- **read**: `004276a0`. The decompiled routine bears out the form of the description: a test of squared unbalance over (h + constant)² against a sum of three terms, never passed on the first pass, a step scaled by a factor, a stop after 50 passes (100 in the other mode, which the description omits), a stop on a large step. The values of the constants (10⁻⁶, 1, 1000, 0.5, 0.1 mm) are not in the file, so the width of the tolerance is not borne out. The routine calls `00427cd0` and `004267c0`, neither given.
- **inferred**: Response accepts the high, barely balanced state at stage 12 (55 N m is inside the 40 to 130 N m quoted) and r2c does not, because r2c's stiffness and step differ from Response's. Nothing in the file tests this.
- **inferred**: the reversed order of "cracking" and "fall" may owe something to how the measure places "cracking". The file does not say how; r2c's "cracking" after its fall is unexplained.

## What the evidence does not establish

- Why r2c left the high state: tolerance, step, stiffness or stage control. Best diagnostic: the trace of tries (`tools/rtrace.py`, `tools/tries.py`) for stages 11 to 13, both programs; none is in the file.
- Whether Response's stage 12 is the uncracked state at all. Best diagnostic: "r2c in Response's own state" at stage 12; not run (the columns are blank).
- How the measure places "cracking" and "fall". Best: the measure's own per-stage output of the features for both curves.
- Whether the 40 to 130 N m figure is sound: it is the developer's statement, with no output shown.
- Response has 31 stages, r2c 29, differing at the end (1.519, 1.524, 1.526 against 1.528). Both read "standing still"; not examined.

## Against the targets

Shape on a case without shear is a **Must**, always assessed, and is not a number: it is outside. The numbered checks on this case are inside the 5 % target (peak 0.21 %, rising branch 0.48 %, post-peak 0.22 %). The load difference at the one stage is 10.5 % of the peak, which the rising-branch measure does not register because the curves are one small control step apart. D54's instability rule does not apply to curve checks.

## On the developer's reason

1. **Partly supported.** The curve listing shows Response with one more rising point before the fall (stage 12: 276.2 against r2c's 239.09), and peak (0.21 %) and rising branch (0.48 %) inside. That the measure reads the order of cracking and the fall from that point is not shown: the file does not say how the measure places either feature. The mark "measured" is right for the extra point and the two figures; the clause about the measure is inferred.
2. **Does not decide.** The decompiled routine bears out the form of the solve (a tolerance test, a scaled step, a pass limit) but not the values 0.5 or the width of the tolerance, which are constants not given. That Response's states before cracking are unbalanced, and that this is where the extra point comes from, is consistent with `branch.py` (a state at 275.90 kN with 0.055 kNm unbalanced at that control value), but that is r2c's state, not Response's, and no diagnostic shows Response's own unbalance at stage 12. The claim that with the solve switched on the shape is Response's and two Must views go outside is a measured claim with no output in the file; it would be the decisive test, and it is absent. The mark "read" fits only the form of the routine; the origin of the extra point is inferred, and the switched-on result should be marked measured and shown. The evidence file also did not say the rule is switched off in r2c, which my first reading had no way to know.

Verdict: does not decide
Suggestion: take up again - it is a Must check outside target whose claimed cause and claimed fix (the switched-on run, and the two Must views it is said to push outside) are stated but not shown in the evidence, so the acceptance rests on an untested account.
