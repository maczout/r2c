# Independent assessment

## What the evidence shows

- One case, `column-nonly`: axial compression only, no moment or shear, initial or incremental ("The two responses").
- The two control curves are identical to the printed digit up to (-2.225, -16915). Peak differs by 0.00 %, rising branch 0.00 %, and the features are in the same order ("The two responses").
- After the peak they part. Response falls from -16191 to -11914 in one step (-2.261 to -2.29), then declines slowly to -6178 at -3.573, where it stops. r2c falls gradually (-14491 at -2.693, -10340 at -3.258, -8436 at -3.584) and runs on to -9.296, levelling near -3524 (control curves; `curves.py --last 6`).
- At the compared stage, Response's section is not uniform over the depth: concrete stress goes from +1.0 at depth 300, through -50.0 at depth 72.75, to -0.33 at depth -300; principal tensile strain is 1.951 at the top and zero below depth 194; steel stress at a crack is non-zero only in the top bars. r2c's section is uniform: concrete stress -13.086 at every depth, no tensile strain ("The views at the compared stages").
- "r2c in Response's own state" is 0.0 % to 0.6 % on all nine view checks (instances table).
- Spread of Response's load nearby is 1.65 % of peak (instances table).
- A second axial-only case, `newbeam-nonly`, ends at the same control values with loads within about 0.2 % (-1832.4 against -1828.3) (`curves.py … newbeam-nonly --last 4`).

## The reason

- **measured**: The nine view misses are not a fault in r2c's material rules. Given Response's strain state, r2c reproduces Response's charts to 0.0–0.6 % ("r2c in Response's own state"). The misses come from the two programs being in different states.
- **measured**: The states differ in kind. After the peak Response holds a state with strain varying over the depth (tension and cracking at the top, crushing peak near depth 73, bottom almost unloaded); r2c keeps uniform strain (-13.086 at all depths). The 100 % differences are a zero chart against a non-zero one.
- **measured**: The post-peak miss (160.9 %) has two parts: r2c carries more load at the same strain (about -8436 against -6178 near -3.58), and r2c runs to -9.296 where Response stops at -3.573. The measure counts both.
- **inferred**: Response leaves the uniform solution at the one-step fall after the peak and r2c's solver does not follow it. Nothing in the file shows the stage at which Response's views first become non-uniform, or why.
- **inferred**: `newbeam-nonly` agreeing suggests the difference is particular to this section, not to axial-only loading in general. The file does not give either section.
- **read**: nothing. The file gives no rule of the binary, no address and no decompiled routine.

## What the evidence does not establish

- Why Response takes the non-uniform state: a rule of its solver, its stage control, or an accident of numerics. No trace is in the file, though the preamble describes one. A trace of Response's tries across stages 19 to 23 beside r2c's would best settle it.
- Whether Response's state is in equilibrium at zero moment under r2c's rules. The state diagnostic compares views, not resultants. N and M of r2c evaluated in Response's state at stage 41 would settle it.
- Why r2c stops later and Response stops at -3.573: the ending rule of either program is not shown. The same trace, at the last stages.
- Whether this is the circular column of the owner's override ("r2c's uniform post-peak stands"). The file does not give the section's shape. The input's section definition would settle it.
- Why r2c's stage 28 was chosen as "the same feature" when r2c's last stage is 37. It does not change the result here (r2c is uniform at every post-peak stage), but the pairing rule is not verifiable from the file.
- Only four of nine views are printed point by point; the other five rest on the table alone.

## Against the targets

Target is 5 % throughout; the case is `flexure`. Peak, rising branch and shape are inside.

- **Must**, 7 view checks outside: principal tensile strain 100.0 % (20.0×), steel stress at crack 100.0 % (20.0×), principal tensile stress 95.0 % (19.0×), longitudinal concrete stress 73.8 % (14.8×), principal compressive stress 73.8 % (14.8×), longitudinal strain 56.7 % (11.3×), longitudinal reinforcement stress 36.2 % (7.2×).
- **Should**, 2 outside: post-peak 160.9 % (32.2×); average angle 100.0 % (20.0×).
- **Could**, 2 outside: crack widths 100.0 % (20.0×), diagonal spacing 100.0 % (20.0×).

All nine view checks are at Response's last stage, which has no following neighbour, so the instability test does not apply and they stay assessed.

## On the developer's reason

1. **Mostly supported.** The curves agree to the printed digit up to the peak, Response's load falls 26 % in one step (-16191 to -11914), its last-stage views are non-uniform under axial load alone, and r2c's are uniform. Two points are not borne out as written: "every view agrees up to the peak" rests on `tools/viewmisses.py`, whose output is not in my evidence (I can see only that no earlier view check is listed as outside), and "every check outside is at that last stage" leaves out the post-peak check, which is a curve check, not a stage. The mark "measured" is right for the curves and the last-stage views; for the views before the peak it is not verifiable from my file.
2. **Supported, with a count that does not match.** The table gives 0.0 % to 0.6 % on nine view checks, not ten. The conclusion holds for the rules that turn a strain state into views; the diagnostic does not test the solver or whether Response's state balances at zero moment in r2c, so "r2c's rules are not what differs" is wider than what was measured. The mark "measured" is right for the number, too strong for that wider wording.
3. **Does not decide.** My evidence does not say the section is circular, and shows one other axial-only case (`newbeam-nonly`, endings within about 0.2 % in load), not two, with no section shape and no views to show it stays uniform. That the cause "was not found" is consistent with the file, which holds no trace and no rule of the binary; it does not show how far the search went. The override exists in acceptance.md and fits this case if the section is the circular column. The mark "inferred" is right.

Verdict: supports
Suggestion: owner's override - the measured parts bear out that the two programs differ only in the state taken after the peak, which is what the existing override (C2) already covers, provided this section is confirmed as the circular column; the origin in Response remains unknown.
