# Independent assessment

## What the evidence shows

- Two checks are outside, both `transverse_average_bond` on `newbeam-tsfactor-mv`: 6.7 % at stage 12 and 5.2 % at stage 11 ("The instances").
- The misses are local ("The views at the compared stages"):
  - Stage 12: r2c is low by 0.0072 to 0.0088 (about 8 to 11 %) at depths -60 to -105 only. The lower band (-210 to -240) agrees within 0.0005.
  - Stage 11: r2c is low by 0.0025 to 0.0027 at depths -165 to -195. The points at -120 and -135 are identical.
  - The stage 12 band is where the chart was zero at stage 11, so it is newly active.
- The control curves agree at both stages ("The two responses"): curvature 0.422 and 0.556 in both programs, loads 41.419 against 41.418 and 44.914 against 44.931. Mean shear strain differs by one printed digit (0.029/0.030, 0.043/0.044).
- Both stages follow the fall of load from 48.249 to 41.419. Spread of Response's load nearby is 3.53 % of peak, so this is not a flat part of the curve.
- With r2c's rules evaluated in Response's own state, the view differs by 0.0 % (stage 12) and 0.4 % (stage 11) (the table and `startfrom.py`).
- `startfrom.py`: r2c started from Response's previous stage and solved under curvature control reproduces the full miss (5.2 %, 6.7 %) with load within 0.01 % of peak and e0, phi, gam differences printed as zero. Under shear strain control, stage 12 "lands". Stage 11 does not: the bond view is no longer listed, but `stirrup_stress_at_crack` is 8.9 % out.

## The reason

- **measured**: The rule that turns a state into this chart is not the cause. `startfrom.py` and the table give 0.0 % and 0.4 % in Response's own state.
- **measured**: Drift from r2c's own earlier stages is not the cause. `startfrom.py` starts from Response's stage 10 or 11 and still gives 5.2 % and 6.7 % in one step.
- **measured**: The difference therefore arises in r2c's one-stage solution. It reaches the same load, e0, phi and gam (differences 0.0000 to 0.0001 in `startfrom.py`), but a different distribution over the depth: "profile" 1.4 % and 2.4 %.
- **inferred**: Just after the fall at cracking, the section state is sensitive to how the shear strain profile over the depth is solved or ended, and r2c's solution settles on a slightly different profile in the newly cracked band. Nothing in the file tests which step of the solution differs.
- **read**: Nothing. The file gives no rule of the binary, no address and no decompiled routine.

## What the evidence does not establish

- **Which rule of r2c's stage solution differs from Response's.** The trace of tries described in the preamble is not in the file. That trace for stages 10 to 12 would best settle it.
- **Whether the diagnostic reads Response's state well enough.** In Response's own state, `shear_strain` is itself 10.2 % (stage 11) and 5.4 % (stage 12) outside, although it is part of the state read from the charts. The 0.0 % and 0.4 % may be less firm than they look. A layer-by-layer listing of the shear strain profile, Response against r2c, at both stages would settle this.
- **What "profile" and "profile error" measure.** The file does not define them. Shear strain control lands at stage 12 with a larger profile figure (9.3 %) than curvature control, which does not land (2.4 %), so the figure does not track the view.
- **Whether control mode matters.** Landing under shear strain control at stage 12 but not at stage 11 is unexplained. It may be chance.
- **Whether Response is steady here.** The neighbours' views and the result of the instability test are not in the file.

## Against the targets

- `transverse_average_bond` is in the `should` list and this is a shear case, so both checks are Should tier, against `views_pct` = 5 %.
- Sizes: 6.7 % (1.3 × target) and 5.2 % (1.0 × target).
- The stage 11 miss exceeds 5 % of the chart's largest value (0.0026) by 0.0001, one printed digit. The file does not show how the printed-precision floor was applied to it.
- The same case's peak (-0.12 %), rising branch (0.15 %), post-peak (0.32 %) and shape are inside target.
- acceptance.md defines `views_pct` "at the peak". These checks are at the cracking and fall stages. The evidence file's preamble says views are checked at each feature stage; acceptance.md's targets block does not say so.

## On the developer's reason

1. **Supports, with two omissions.** The evidence bears out most of it:
   - The chart's largest values are 0.132 and 0.0521 ("about 0.1" is loose for stage 11).
   - In Response's own state the view is at 0.0 % and 0.4 %.
   - Started from Response's previous stage under curvature control, r2c takes 6 and 8 passes, has profile error 0.86 % and 0.81 %, and is outside on this view only.

   The omissions:
   - Under shear strain control the same diagnostic gives a different result. Stage 12 lands, and at stage 11 the view outside is `stirrup_stress_at_crack` (8.9 %), not this one. "On this chart alone" holds for one control mode only.
   - `tools/sources.py` is not in my evidence file, so I cannot check what rests on it.

   The mark "measured" is right for what `startfrom.py` shows.

2. **Does not decide.** Nothing in the evidence tests it, as the developer says. The mark "inferred" is right. Two facts sit uneasily with it:
   - The difference is not scattered. At stage 12 r2c is low by 8 to 11 % on four adjacent layers (-60 to -105), all of the same sign, while the profile error is under 1 %. The file does not show that a 1 % tolerance allows this.
   - The measure is relative to the chart's own largest value, and the differing points are about 70 % of that value. The chart being small in absolute terms does not by itself explain a 6.7 % relative difference. The difference (0.0088) is far above printed precision (0.0001).

   In its favour, the 0.0 % in Response's own state and the landing under shear strain control at stage 12 fit a difference of solution path, not of rule. Rerunning `startfrom.py` with a tighter iteration tolerance would settle it.

Verdict: does not decide
Suggestion: keep accepted - the deviation is small, in the Should tier and openly recorded, but its cause is untested, so it should stay assessed and not be dropped on the unproved ground that the chart is small.
