# Independent assessment

## What the evidence shows

- One check is outside: shape, on `newbeam-tstiff6-mv` (M + V). Response: cracking, peak, ends falling. r2c: cracking, fall, peak, ends at peak ("The instances").
- The two curves agree to about 0.2 % of load through stage 31, including Response's peak (219.30 against 219.64 at curvature 4.254) and the drop to 192.7 at 4.680 ("The two responses"; `curves.py`).
- After stage 31 they part. Response: 192.85, then 212.48, both under its peak. r2c: 219.59, 221.63, 222.63, the last two above its stage-30 load of 219.64 (`curves.py`).
- `tries.py`: 33 tries agree. For stage 32 both programs try curvature 5.1477, 4.8925 and 4.7638, and both end each at 16 passes with a load near 220 and an error of 7 to 9 %. On the third, Response does not keep it ("16 passes above", 219.48, 8.54 %); r2c keeps it (219.59, 8.25 %). Response then tries 4.6994, which solves in 4 passes at 192.85 (0.77 %) and is kept. r2c never makes that try.
- The one rule given, `004ac960`, is the slopes of the concrete stress. Its measurement (`flowset.py`) does not name this case.

## The reason

- **measured**: the shape differs only because r2c's last two stages rise 1.4 % above its stage-30 load (222.63 against 219.64, `curves.py`). The measure then reads stage 34 as the peak, the drop at stage 31 as a fall before the peak, and the ending as "at peak". Up to stage 31 the features are the same.
- **measured**: the split starts at one try. At curvature 4.7638 both programs reach nearly the same unsolved state (219.48 against 219.59, 8.5 against 8.3 % error, 16 passes); Response rejects it and r2c keeps it (`tries.py`, row 33). So the difference there is in the decision to keep a stage, not in the section's calculated state.
- **inferred**: r2c's rule for keeping or refusing a try differs from Response's here. The file holds neither rule. r2c refused 7.56 % and 7.80 % but kept 8.25 %, so it is not a plain error limit.
- **read**: `004ac960` is not shown to bear on this check. The decompiled routine bears out part of its description: the softening slope is zero for models 0, 1, 3, 8 and 11, zero at the bounds for 6 and 7, and model 5 has the negated form with a 1 added. The constants are not visible, and the compressive-strain part and the caller's ratio are in the 90 lines cut or absent, so these are unconfirmed.

## What the evidence does not establish

- Why r2c kept the try. Missing: Response's stage-control routine (address and code) and r2c's rule beside it. That is the diagnostic that would settle it.
- Whether r2c, made to take the 4.6994 try, would solve at about 192.85 and then follow Response. A forced run from that try would settle it.
- Whether the slopes rule contributes. Row 31 gives a hint only (15 passes and 0.81 % against 16 and 1.44 %). A run with the slopes rule off on this case would settle it.
- The trace is not reference data. Its last Response row (4.7638, 214.14, "?") does not match the record's last point (4.981, 212.48), and the stage counts differ (32 against 33). Response's result under the tracer may not be the recorded one.
- What "16 passes above" and "?" mean is not defined in the file.

## Against the targets

- Tier: Must (shape, always assessed, no number). It is outside.
- Peak +1.52 % and rising branch 0.09 % are inside the 5 % target. Post-peak is 7.67 %, outside, but not in this group.
- The case is a shear case. acceptance.md says that for a shear case "shape" leaves out how the response ends, and that shear endings are Won't. All the difference arises after Response's peak, yet it changes the feature list before r2c's peak (a "fall" appears). Whether that counts as the ending is not settled by acceptance.md; it is for the owner.

## On the developer's reason

1. **Supported, with one inexact count.** `curves.py` shows the same top (219.30 against 219.64), the same fall (192.68 against 192.69), r2c rising past its first top (222.63) and the peak therefore read after the fall. But Response's record has two stages after the fall (192.85 and 212.48), not one. The mark "measured" is right.
2. **Not decided.** Nothing in the evidence file compares r2c with and without the slopes rule on this case, and `flowset.py` does not name the case. The mark "read" is wrong: that r2c's behaviour changed when the rule went on is a claim about two runs of r2c, which a routine of the binary cannot show; it should be "measured" with the runs given, or "inferred" without them. The routine itself is only partly borne out by the decompiled code (see above).
3. **Not decided as to cause; the description is partly contradicted.** The mark "inferred" is right, and the developer says it was not looked into. But the evidence does bear on it: Response does not simply stop while r2c goes on. `tries.py` puts the split at stage 32, where both programs reach the same unsolved state at curvature 4.7638 (16 passes, error above 8 %) and r2c keeps it while Response rejects it and solves a smaller step at 192.85. Response then has a further stage (212.48 at curvature 4.981, beyond r2c's last curvature of 4.668). r2c has one stage more than Response in number, but the two part two stages before Response's last. So "r2c carries on after Response's last stage" does not describe what the record shows. Whether a kept-or-refused try three stages from the end is "how a shear response ends" is a question of the targets, for the owner.

Verdict: does not decide
Suggestion: take up again - the trace places the split at a single decision to keep an unsolved try that Response rejects, which is a rule of the stage control that can be read and checked, and the developer's account neither looked into it nor tested its one causal claim.
