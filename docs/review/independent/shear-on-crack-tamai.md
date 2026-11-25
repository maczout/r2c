# Independent assessment

## What the evidence shows

- One check is outside: `shear_on_crack` on `newbeam-tstiff4-mv`, Response's stage 38 (peak) against r2c's stage 40; 10.4 %, largest difference 0.3553 on a chart maximum of 3.4055 ("The instances").
- The two stages are at the same place: both at (4.744, 193.14) on `moment_phi` ("The two responses"; `curves.py --last 10`).
- 0.3553 is exactly the difference of the two charts' largest values on line 2: Response -3.4055 at depth 181.14, r2c -3.0502 at depth 180.13 (`viewlines.py --raw`).
- On line 2, Response's values are non-zero from 181.14 downward and stand high (3.41 to 1.88) over seven points, 181.14 to 179.13. r2c's are zero at 180.80 and 180.47 and stand high (3.05 to 2.58) over three points, 180.13 to 179.46. From 178.79 downward the two agree to about 0.02 (same diagnostic).
- Line 0 shows the same: Response about -0.20 from 180.80 to 179.46 and -0.16 at 179.13; r2c about -0.20 from 180.13 to 179.46 only. At 181.14 Response has line 2 at its maximum with line 0 at zero; r2c has no such point.
- The depths of the points differ near there: Response has points every 0.335 from 181.81 to 176.79; r2c every 0.335 only from 180.80 to 178.12, and r2c has points (166.07, 155.36) where Response has none and lacks Response's 107.14 and 64.29 (same diagnostic).
- With r2c's rules in Response's own stage-38 state, `shear_on_crack` differs by 18.44 %; every other view is at 0.90 % or less except `transverse_average_bond` (4.87 %); M differs by -0.00 %, V by +0.05 % (`diagnose.py states --stages 38 --views`).

## The reason

- **measured**: the miss is not a matter of which stage is compared or of the state reached. `diagnose.py states` gives 18.44 % in Response's own state, larger than the 10.4 % of the run, while strains, crack widths and angle there are within 0.06 %.
- **measured**: the miss is confined to about 2 mm of depth, 181.14 to 179.13 (`viewlines.py`). There Response's band of high values is about 2 mm deep and starts about 1 mm higher than r2c's, which is about 0.7 mm deep; r2c's top value is 0.3553 lower.
- **measured**: the two programs do not place their points at the same depths around that band (`viewlines.py`).
- **inferred**: r2c either starts this band at a different depth, or lays out its layers differently there, or evaluates the top point of the band by a different rule (Response's point with line 2 at maximum and line 0 at zero). The file cannot separate these.
- **read**: nothing. The file gives no rule of the binary and no address.

## What the evidence does not establish

- What lines 0 and 2 are, and what lies at depth 179 to 181 (a change of width, a bar, the edge of cracking). Missing: the section and the chart's legend.
- Whether the differing layer depths cause the miss or accompany it. Best diagnostic: r2c's view computed on Response's own depths at stage 38, point by point.
- Where the 18.44 % lies; `diagnose.py` prints only a total. A point-by-point listing of that in-state chart would settle whether it is the same band.
- Whether the "own state" was read closely enough at a band 2 mm deep; the file itself allows this as a cause of a large figure.
- Whether the band is there at other stages. Only stage 38 is shown; stage 37 on both sides is needed.
- The instability test's result is not shown; the check is counted as assessed.

## Against the targets

- `shear_on_crack` is in the `should` list, on a shear case: tier Should.
- 10.4 % against `views_pct` 5 %: 2.1 times the target. One check, one case.
- The largest difference, 0.3553, is far above the printed-precision floor (two units of 0.0001).
- The same case's post-peak (9.38 %) and ending (falling against standing still) are not in this group; endings of shear responses are a Won't.

## On the developer's reason

1. **Partly supports, partly contradicts.**
   - "Outside in Response's own state too, and by more": supported, 18.44 % against 10.4 % (`diagnose.py states`).
   - "The line jumps from nothing to several MPa at the top of the cracked zone": supported, 0 to -3.4055 in Response and 0 to -3.0502 in r2c (`viewlines.py`). That line 2 is "the limit" is not in my file.
   - "One node lower in r2c": not borne out as stated. Response's jump is at 181.14 and r2c's at 180.13, about 1 mm; r2c is zero at two of its own nodes (180.80, 180.47) where Response is not, and r2c has no node at 181.14 at all. A jump merely moved down would also keep its height and its extent; r2c's top value is 0.3553 lower and its high band is three points against Response's seven.
   - "Flat over seven stages": supported near enough; Response's stages 32 to 38 lie between 192.96 and 193.14.
   - The mark: *measured* is right for the first, second and fourth; "one node" is a reading of the chart that the chart does not give. `tools/sources.py` is not in my file, so I cannot check what rests on it.
2. **Does not decide.** Nothing in the file tests whether this is one misplaced node or a rule; the developer says so. What the file does show leans against "one node and not a rule": a different top value, a band of a different depth, layers at different depths, and Response's top point with line 2 at its maximum and line 0 at zero, which r2c has no counterpart to. The reading that the charts give the state only node by node is possible and the file allows it, but it is not shown. The mark *inferred* is right.

Verdict: does not decide
Suggestion: take up again - the reason offered is untested, its one checkable detail (one node) is not what the chart shows, and r2c's view on Response's own depths at stage 38 would settle whether this is layering or a rule.
