# Independent assessment

## What the evidence shows

- One check is outside: the shape of `igirder-mv`. Response: peak, ends falling. r2c: fall, peak, ends falling ("The instances").
- r2c has three stages Response's reference lacks, at curvatures −0.539, −0.533 and −0.532 with loads 49.54, 51.80 and 32.46. Response goes from (−0.571, 30.92) straight to (−0.530, 34.55). The fall is 51.80 to 32.46 ("The two responses").
- Trace (`tools/tries.py`): tries 0 to 5 agree. At try 6, target −0.5385, Response has "dropped: no solve" (load 38.95, err 7.45 %); r2c has "kept" (load 49.54, err 0.61 %). r2c then keeps two more tries, at −0.5320 and −0.5334; Response moves on to −0.4113.
- `tools/repeat.py`: Response does not repeat. Five runs gave 15 stages (peak 12) twice and 25 stages (peak 22) three times. The reference is the 15-stage result.
- Peak differs by −0.01 %, rising branch 2.40 %, post-peak 4.09 % ("The two responses").

## The reason

- **measured**: the fall in r2c's curve is the three extra stages near −0.53. `tools/curves.py`: 51.8 at −0.533, then 32.5 at −0.532, a drop of 19.3, about 2.9 % of the peak.
- **measured**: those stages exist because r2c solves a try that Response does not. `tools/tries.py`, try 6: Response not solved at err 7.45 %, r2c kept at err 0.61 %. The same target is tried by both, so the control of the stages agrees up to there; the solve of that one try is what differs.
- **read**: rule `00415e30` says a stage put in between that is not solved is dropped and the stage set aside is taken up. That matches what Response does at try 6. The decompiled routine bears out part of the description: stages are compared, an event type is set, a stage is put in, and type 2 starts from the other stage's profile. It does not show the dropping, which is given to `00418af0`, and that routine is not in the file. Which event type is "un-cracked" cannot be checked from the listing either.
- **inferred**: r2c's solver converges at that try where Response's does not, by a different first estimate, iteration limit or convergence test. Nothing in the file tests which.

## What the evidence does not establish

- Why Response's try fails. No rule or diagnostic covers its solve. Best diagnostic: the iterations of try 6 in both programs, with the first estimate and the convergence limit.
- Whether Response always drops that try. It does not repeat, and the tracer can change its result; one trace is shown. Best diagnostic: the curve of the 25-stage result, and the trace repeated. From the stage counts I infer the 25-stage result adds only the ten stages between 366 and 462 that r2c also has, but its curve is not given.
- The rule's note reports Response keeping stages at 49.6, 51.8, 32.6 and 34.5 on "M/V = 2 m", nearly the same numbers as r2c gives here at M/V = 1 m. Either Response does solve this try on a neighbouring case, or the note names the wrong case. The file does not settle it.
- What "err %" and "ps" measure, and the limit a kept try must meet.
- r2c lacks Response's last stage (−0.476, 140.63). It is not part of this check.

## Against the targets

- Tier: Must. Shape must be inside on every case (phase A exit criteria).
- Shape is not a number: the features in order must be the same. They are not, by one fall before the peak. Outside.
- The case has a shear increment. For shear cases shape leaves out the ending; the miss is before the peak, so that does not cover it.
- The instability rule (D54) applies to views only, not to curve checks, so Response's failure to repeat does not exempt this check.
- The numeric checks are inside ±5 %: peak −0.01 %, rising 2.40 %, post-peak 4.09 %.

## On the developer's reason

1. **Supported in part.** `tools/curves.py` shows the stages put in between, the fall (51.8 to 32.5, about 2.9 % of the peak) and agreement before and after. It does not show that the top is cracked under no load, that the cracks close there, or that r2c's stages are "still cracked"; and the 2 % the measure counts is not in my evidence. The mark "measured" is right for the curve and too strong for the crack states, which are inferred here.
2. **Supported.** The trace (`tools/tries.py`, try 6) shows directly that Response tried −0.5385 and dropped it unsolved (err 7.45 %) while r2c kept it (err 0.61 %). The mark is not the best one: the developer deduces the failed try from the rule, but it is measured; and the dropping itself is given to `00418af0`, which is not in the file, so "read" is only partly borne out by the decompiled `00415e30`.
3. **Supported in part, otherwise not decided.** `tools/repeat.py` gives 15 stages twice and 25 three times: measured. That the ten more belong to the web cracking, and that no capture has a stage at the closing of the top cracks, is not in its output; the 25-stage curve is not given. The counts and r2c's ten stages between 366 and 462 are consistent with it, no more. Those two claims should be marked inferred.
4. **Not decided.** The mark "inferred" is right, and the admission that the cause was not read is accurate. But "not set by the input alone" has nothing behind it. If part 3 is right that no capture has a stage there, Response fails at this try every time, which points to a repeatable rule of its solve rather than to chance.

Verdict: supports
Suggestion: take up again - the check is a Must, the mechanism is measured but its cause is not read, and Response's failure at this try appears repeatable, so it is likely a rule of the binary's solve that one diagnostic (the iterations of try 6 in both programs) could find.
