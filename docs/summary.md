# r2c: the owner's summary

**Read this first.** The one page the owner reads each session: where r2c stands, what
"finished" means, and every decision that is open or has been made. The developer keeps it
current at the end of every session (CLAUDE.md, "Ending a session"). Everything else in
`docs/` is the developer's working record and backs this page; it does not replace it.

Last updated: 2026-11-22, by the developer, at the end of the session on step A-1b (log
2026-11-22-08).

**What changed.** Step A-1b, the three parts the owner set (D45). (1) The measure now
compares views at r2c's stage at the same place as Response's, where there is one (D42):
the column with shear is no longer compared four stages apart. (2) The reading of
Response's stage control was taken as far as two approaches go. Two of its rules were
verified against Response's own stages and are in use. **The shape of the I-girder with
shear is not resolved:** Response keeps the stages in question on every case of that
girder at M/V = 2 m, where r2c now has them exactly, and drops them at M/V = 1 m; why
was not found (D48). (3) The crack spacing over the depth was read from the program and
reproduces Response's charts to 0.001 mm on all three new shapes. The transverse table is
in use; **the longitudinal table is written and switched off**, because with it the last
stage of one Newbeam shear case lands on the measure of the rising branch, a Must (D46).

**Three items wait for the owner: D46, D47, D48.** D46 is the one that holds back the
most: 43 checks, and the last view outside on a Must that is a known deviation (D35).

## Aim

A really good sectional response calculator, interchangeable with r2x. **What exists** is
judged against Response-2000 as documented (the manual, Appendix A of Bentz's thesis).
**How it calculates** is the 1.9.7 program's, read from the binary: where the thesis and the
binary differ, the binary is followed without asking, apart from the owner's overrides in
`docs/acceptance.md` (D34). Bells and whistles are built outside r2c and r2x. (Owner,
2026-11-22.)

## Phases

| Phase | What | State |
|---|---|---|
| **A. Develop the kernel** | On a development set that widens step by step (D41): Newbeam varied in its loads (the 17 cases below), then one variable at a time — shape (step A-1, the seven Quick Define cases), then reinforcement, material models, units and material factors. What is not yet in the set stays parked. | **Now.** Step A-1 (shape) and its follow-up A-1b are worked through (2026-11-22). On the 24 cases peak and rising branch are met; shape on 21 and the Must views on 11 of 13. Of the five misses four are known deviations or the owner's override (D32, D36, D35, C2) and one is the shape of the I-girder with shear (accepted for now, D43; still open, D48). The Should on shear views is met on 3 of the 11 shear cases |
| **B. Validate and refine** | The parked cases come back; the test set and targets are reviewed; r2c is held to them. | Not started. Starts when the development set has widened to cover the scope and meets the exit criteria (D1, D2). Then the test set and targets are reviewed with the owner. |

### The development set

**Newbeam (17 cases).** Newbeam as Response defines it, in SI units, with no material factors; only the loads
differ. Confirmed against the fixtures on 2026-11-22: 17 cases.

| Without shear (8) | With shear (9) |
|---|---|
| M | M + V at M/V = 0.5 m |
| −M | M + V at M/V = 1 m |
| N (compression) | M + V at M/V = 2 m |
| N (tension) | V alone |
| N + M increasing together | constant N (−500 kN), then V |
| constant N (−2000 kN), then M | constant N (−500 kN), then M + V |
| constant N (+200 kN), then M | N + M + V increasing together |
| no load | constant M (−50 kNm), then M + V |
| | constant V (50 kN), then M |

**Step A-1, shape (7 cases, owner 2026-11-22, D41):** the Quick Define sections already among
the fixtures — T-beam under M and −M (`tbeam-m`, `tbeam-negm`); column under N, N₀ + M and
M + V (`column-nonly`, `column-n4000-m`, `column-mv`); I-girder under M and M + V
(`igirder-m`, `igirder-mv`). The column under N alone carries the owner's override after its
peak (C2, D12).

All seven have joined the set (owner, 2026-11-22, D44).

Parked, kept and not run by default (61 cases): other materials and reinforcement, units,
material factors, More Detail, no input, the other cases on the T-beam, column and
I-girder, and Response's sample inputs. They sit in a folder of their own and can be run on
request. Eleven of them need something that has been removed, and r2c refuses them: five
since the removals of D18, six more (all on Response's sample inputs) since D23.

## Progress against the Phase A exit criteria

Cases inside target, counted by `tools/targets.py --counts` from the run of record of step
A-1b (2026-11-22, `docs/verification-results.md`). "Before" is the run of the same 24 cases
on the kernel of step A-1, measured with the stage matching of D42. (D42 itself, on that
kernel: the Could views went from 14 to 15 of 24 cases; check by check 44 came inside and
4 went outside, as foreseen: `docs/verification.md`, "Step A-1b".)

| Check | Before | Now | Exit tier (D1, D2, D27) |
|---|---:|---:|---|
| Peak | 24 of 24 | 24 of 24 | Must: met |
| Rising branch | 24 of 24 | 24 of 24 | Must: met |
| Shape | 21 of 24 | 21 of 24 | Must (a shear case's ending left out: D25). Two misses are known deviations (D32, D36); the third is the I-girder with shear (D43, D48) |
| Views of the stress state, without shear | 11 of 13 | 11 of 13 | Must. The misses: a known deviation (D35; it comes inside with D46) and the column under N alone after its peak (the owner's override, C2) |
| Post-peak, without shear | 12 of 13 | 12 of 13 | Should. The miss is the column under N alone (C2) |
| Views related to shear, and stress-state views with shear | 14 of 24 (2 of the 11 with shear) | 15 of 24 (3 of the 11 with shear: the I-girder with shear came in) | Should, not met |
| Views related to cracking | 15 of 24 | 15 of 24 (20 of 24 with D46) | Could |

Check by check over the 24 cases, 14 came inside and one went outside (shear stress at the
flat peak of the column with shear, 2.9 to 7.7 %, a Should).

### Step A-1b, part by part

| Part | What was done | Outcome |
|---|---|---|
| 1. The measure (D42) | Views are compared at r2c's stage at the same place as Response's feature stage (within the target in load and control value together), and at the stage of the same feature only where there is none. Never across a fall of load: where the two curves have the same falls, only stages with as many falls behind them are looked at (D13's purpose, kept explicitly) | **Done**, in its own commit; the "before" run recorded. Listed in the pull request under "Measurement changes" |
| 2. Response's stage control (D43) | Read: how the program tests "cracked" between two stages; what it starts a stage put in between from; what it does when that stage fails; its solve of a stage, which was written out in r2c and tried | **Two rules in use, each checked against Response's own stages** (below). **The I-girder's shape is not resolved** (D48). The program's solve is written and off: it moves checks both ways and changes nothing here |
| 3. Crack spacing over the depth (D45) | Read: how the program tabulates both spacings (bars around a circle, hoops, the ends of a stirrup, a step in width) | **Reproduces Response's charts within 0.001 mm** on the column, T-beam and I-girder (they were 21, 11 and 6 to 8 % off). **Transverse table in use**; longitudinal table written and off (D46) |
| The two shear cases on their views | Judged after part 3 | **I-girder with shear: Should views met** (every assessed view inside, the worst 2.5 %). **Column with shear: not met**, at its peak only (D47) |

**The two stage control rules now in use.** (a) Between two stages the program asks
whether the section has cracked using the cracking strain before it is lowered for
compression. r2c used the lowered one, and so closed in on the first node to crack under
compression, which the program does not: under V with constant compression r2c had seven
stages there that Response has not. (b) A stage put in between two others starts from
whichever of the two is nearer, and is dropped if it fails. On the I-girder at M/V = 2 m
(parked) Response's three stages around the closing of the top cracks are now r2c's, at
the same curvatures and within 0.1 kNm. Neither moved any check on the 24 cases to the
other side.

**Whether it explains the parked I-girder that ended early (softening 6, M/V = 2 m): no.**
That case ends early because r2c refuses a stage just after the web cracks whose shear
profile it cannot settle (9 % off after sixteen passes, with the load above the largest
so far), where Response keeps a stage with a lower load. It is the profile iteration at
that state, not a rule of the stage control read here. The early end has moved to other
parked cases of the same girder (Risks).

### The seven new cases

| Case | Musts | Should | What is left |
|---|---|---|---|
| T-beam, M | met | met | Longitudinal crack spacing 7 % (Could; D46) |
| T-beam, −M | met | met | Longitudinal crack spacing 6 to 8 % (Could; D46) |
| Column, N alone | met up to the peak | met up to the peak | After the peak: the owner's override (C2, D12). Longitudinal crack spacing 21 % (Could; D46) |
| Column, N₀ = −4000 kN, then M | met | met | Longitudinal crack spacing 21 % (Could; D46) |
| Column, M + V | met (peak, rising branch, shape) | **views not met, at the peak only** | At cracking every Must and Should view is inside since D42. At the peak ten views are 8 to 14 % off: the two programs are in different states on a flat top (D47). Longitudinal crack spacing 21 % (D46) |
| I-girder, M | met | met | One cracking view at 5.1 to 5.3 % (Could; it comes inside with D46) |
| I-girder, M + V | **shape not met** (accepted for now, D43); peak +0.06 %, rising branch 2.4 % | **met** | D48 |

### Which known deviations recur on the other shapes

The owner asked for this (D41): a deviation that recurs is likely Response's solver; one
that does not was a Newbeam quirk.

| Known deviation (on Newbeam) | On the seven new cases |
|---|---|
| How a shear response ends (a Won't, D1) | **Recurs on both** shear cases: Response's ends falling on a stage it has not converged, r2c's stands still (column) or falls one stage earlier (I-girder) |
| A peak reached in a slightly different state (three Newbeam shear cases) | **Recurs** on the column with shear: the top of the curve is flat within 0.2 % over three stages, and at the same curvature the two programs' states differ by 8 to 14 % on ten views (D47) |
| D32: a fall of load just under the 2 % the measure counts from (V alone) | Does not recur. The I-girder with shear has a fall the other way round: r2c has one of 2.9 % where Response has none (D43, D48) |
| D35: one point at the crack front at the last stage, without shear | Does not recur: the five new cases without shear are inside at their last stage (the column under N alone apart) |
| D36: tension's shape | Not tested: no new case is under axial tension |
| D38: a limit line of shear on the crack that one program draws and the other does not | Does not recur |
| D39: the stirrups' memory of yielding (off) | Does not recur: switched on, it moves no check on either new shear case to the other side (measured). Neither has the fall and recovery on the way up that M/V = 0.5 m has |
| C2: the column under N alone after its peak | It is this case; unchanged |

Every rule taken over is in `docs/kernel.md` with its source. Increment A4 is in the log
of 2026-11-22-06.

Known deviations are in `docs/status.md`: how shear responses end (a Won't, D1), the
circular column under axial load alone, which is not cloned (D12), the fall of load
before the peak under V alone (D32), tension's shape (D36), and the last-stage point on
"constant N +200 kN, then M" (D35), and the shape of the I-girder with shear (accepted for
now, owner 2026-11-22, D43; D48). Put to the owner in step A-1b: the views of the column
with shear at its peak (D47).

### What was removed (D18)

Each item of the scope inventory is now marked as documented or not, with the manual's page
(`docs/scope.md`). Removed, and now refused as out of scope: draped tendons (D4); the Hsu
softening models combined with Tamai tension stiffening (D5); compression softening 4 (D10),
16 and 17 (later than the manual); a segmental stress-strain curve for reinforcing steel. A
shape with no outline is an input error (D6). Response's program folder was never read, and
is not (D9). Three things were unclear and were put to the owner: the eleven softening models the manual names are kept (D21); 1.9.7's defaults are followed (D22); several sections in one file and the horizontal tie are refused (D23, done 2026-11-22).

## Decisions

Numbered once and never renumbered. The developer adds a question here, with a suggested
answer, instead of leaving it only in a session log; a log refers to it by number. The owner
answers here (or in conversation, and the developer records it here with the date).

**Status:** *decided* (owner, with date) · *suggested* (the developer's answer, awaiting the
owner) · *open* (no suggestion yet).

### Steering

| # | Question | Status | Answer |
|---|---|---|---|
| D1 | What "finished" means for Phase A | decided, owner 2026-11-22 | *Must:* peak, rising branch and shape inside on every case. *Should:* the endings of moment (and axial) responses inside on every case. *Won't:* shear endings; recorded as known deviations. |
| D1a | Reading of D1: "shape" for a shear case leaves out how the response ends, since the ending is a Won't | decided, owner 2026-11-22 (suggestion approved) | Yes |
| D2 | Detail views and post-peak: chase them? | decided, owner 2026-11-22 | *Must:* views of the stress state under moment and axial load. *Should:* views related to shear. *Could:* views related to cracking. |
| D3 | Shear endings: chase further or accept? | decided, owner 2026-11-22 | Accept: see D1 (Won't). |
| D20 | `docs/acceptance.md` still says "where r2c and Response differ, Response is right", with no qualifier | decided, owner 2026-11-22 (suggestion approved) | Reworded: "Response as documented is right; undocumented solver behaviour is not cloned"; the tiers of D1 and D2 added as the phase A exit criteria. Done 2026-11-22. The first half is superseded by D34. |

### Scope

| # | Question | Status | Answer |
|---|---|---|---|
| D4 | Draped tendons (rule not found; effect under 0.1 %) | decided, owner 2026-11-22 | Out of scope |
| D5 | Hsu softening models with Tamai tension stiffening | decided, owner 2026-11-22 (suggestion approved) | Out: a research feature, not the calculator |
| D6 | A shape with no outline (Response cannot solve it; r2c builds it) | decided, owner 2026-11-22 (suggestion approved) | Reject it, as Response does |
| D7 | Inputs Response rejects are input errors in r2c | decided, owner 2026-11-22 (suggestion approved) | Confirm |
| D8 | Two added scope statuses, "no effect" and "not solvable" | decided, owner 2026-11-22 (suggestion approved) | Confirm |
| D9 | Response's program folder (`rebar.dat`, `r2k.r2k`): should r2c read it? | decided, owner 2026-11-22 (suggestion approved) | No: outside the calculator |
| D10 | Compression softening 4 ("Unsupported Method") | decided, owner 2026-11-22 (suggestion approved) | Out: undocumented |
| D11 | Interlocking hoops analysed as stirrups (inferred, within 0.8 %) | decided, owner 2026-11-22 (suggestion approved) | Confirm |
| D12 | Circular column under axial load alone after its peak (C2) | decided, owner 2026-11-22 | Looks wrong in Response: not cloned; r2c's uniform post-peak stands. Pure N stays in Phase A on Newbeam. |
| D17 | Which document defines a complete feature | decided, owner 2026-11-22 (suggestion approved); amended by D34 | The manual (thesis Appendix A) for which features exist; ~~the thesis~~ the binary for how they calculate (D34) |
| D18 | Features built beyond the documented set (less common softening models, segmental steel, …) | decided, owner 2026-11-22 | Remove the code |
| D21 | Compression softening models that the manual names but that neither the manual nor the thesis gives a rule for (eleven of them: Vecchio-Collins 1982, 1992-A and 1992-B, Mehlhorn, Maekawa, Noguchi, Belarbi-Hsu, Collins 1978, Kaufmann-Marti, Hsu-Zhang 1998, Hsu 1993). Their rules in r2c were read from the binary. D18 names "less common softening models" for removal; the manual lists them, so they were kept | decided, owner 2026-11-22 | **Keep them.** Being named in the manual counts as documented; their rules from the binary stay. (The developer had suggested removing them.) |
| D22 | The default compression softening of Response 1.9.7 (Collins-Bentz 2011) is later than the manual and the thesis, so by D17 it is not documented. Every case uses it. For Newbeam's concrete it is the thesis' own equation; they differ above 57 MPa. The automatic tensile strength is another default where the program differs from the thesis | decided, owner 2026-11-22 (suggestion approved) | Keep. Where a default of Response 1.9.7 differs from the 2000 documents, r2c follows the program, because the oracle runs with its defaults |
| D23 | Two things an input file can carry that the manual does not have, and that r2c reads as the nearest documented thing with no code of their own: several sections in one file (the first is read), and the horizontal tie (read as a stirrup). Both occur only in Response's sample inputs, which are parked | decided, owner 2026-11-22 | **Refuse them now**, with a reason, as for the other removals (D24). (The developer had suggested leaving them until phase B.) **Done 2026-11-22:** the six parked cases on Response's sample files that hold several sections are refused and kept |
| D24 | Reading of "out of scope" and "remove" (D4, D5, D10, D18): r2c refuses such an input and says why, where before it read a drape and ignored it, or ran a Hsu model with Tamai tension stiffening as two independent models | decided, owner 2026-11-22 (reading confirmed) | Yes: refuse, do not ignore silently |

### Measurement and test set (meta-development)

| # | Question | Status | Answer |
|---|---|---|---|
| D13 | Stage matching: a 0.5 % change in r2c's load can switch the matched stage and flip 11 view checks | decided, owner 2026-11-22 (suggestion approved) | Fix the measure before any work on views. **Done 2026-11-22:** a stage is matched between the same features of the two curves. Without shear only the no-load case's first stage was re-matched, and no check changed; with shear ten stages, mostly after the peak, are now matched to like states (one had been matched to r2c's stage 1) |
| D14 | F1: Response's cracking-under-compression rule inside the node | decided, owner 2026-11-22 (suggestion approved) | Yes, after D13. **Done 2026-11-22** (A2 part 2) |
| D15 | The generated results JSON is committed on every run (~80,000 lines) | decided, owner 2026-11-22 (suggestion approved) | Build it in CI instead of storing it |
| D16 | The test set has grown to 85 cases | decided, owner 2026-11-22 | Develop on Newbeam; the rest is parked until Phase B. Amended by D41: the set widens step by step within phase A |
| D19 | Parked fixtures: delete, or keep and not run by default? | decided, owner 2026-11-22 (suggestion approved) | Keep them, not run by default |
| D25 | The shape check still counts how a shear response ends, against D1a. Two cases (M/V = 0.5 m and 2 m) are outside on shape for that reason alone | decided, owner 2026-11-22 (reading confirmed) | Change the measure so that shape leaves out the ending for shear cases. **Done 2026-11-22:** shape 13 → 15 of 17 |
| D27 | Which of the 21 detail views are Must, Should or Could | decided, owner 2026-11-22 | Must: the stress-state views on cases without shear, including steel stress at a crack and the principal tensile strain and stress (the owner's choice). Should: shear views, and stress-state views on shear cases. Could: cracking views. Lists in `docs/acceptance.md` |
| D28 | Bounds, in case a Must is harder than it looks | decided, owner 2026-11-22 | Two grounded approaches per part at most, no tuning to fit, no regression; on stopping, put it to the owner with options. In `docs/acceptance.md` |

### Left by increment A2 (answered 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D29 | Reading of the no-regression bound (D28: "no Must view that is inside may go outside"). With Response's layering, principal tensile stress on M went from 18.2 to 0.0 % at the peak and from 4.2 to 7.2 % at the last stage. The developer read the bound view by view on a case, as the report counts it: that view on M was outside before and is outside now, so the layering was kept. Stage by stage it is a regression | decided, owner 2026-11-22 | **Confirmed: the binary's layering stays.** Under D34 the stage left on M (7.2 %) is not a known deviation; it is work in increment A3. (The developer had suggested: Confirm, and accept that stage as a known deviation. At that stage r2c has Response's points, and gives Response's forces in Response's own state; the two states differ by 0.005 mm/m of strain, less than Response's own solve leaves unbalanced, and next to a crack front that is 7 % of the chart. Other options: take the layering out again (the four stages that came inside go back out), or measure this view differently at a crack front (meta-development, with the owner)) |
| D30 | Where no bar crosses the cracked zone (under N + M the zone is below the bottom bars), the thesis says the concrete tension is not reduced; Response 1.9.7 reduces it to the floor it keeps after cracking. r2c follows the thesis. This is the one principal-tension miss left that has a rule behind it: N + M at cracking, 51.5 % | decided by D34 (owner 2026-11-22) | **Follow the program** (D34: the binary is followed where it and the thesis differ), as for the defaults in D22: the oracle runs the program. Tried and not kept: 51.5 to 0.3 %, nothing else moves, the Must views go to 6 of 8. One line of code |
| D31 | Tension's shape (A2 part 4, stopped). Response's curve has one more rising point before the fall at cracking than r2c's (276.2 against 274.5 kN; r2c's own limit is about 275.6), and the measure reads the order of cracking and the fall from that point. Response's solve carries on with a state it has not balanced; r2c finds none there | decided, owner 2026-11-22 | **Clone it.** Under D34, cloning how Response's solve gives up at cracking under tension is allowed. It is work in increment A3, not a known deviation. (The developer had suggested: Accept as a known deviation. Other options: read cracking and a fall at the same step as one feature (a change to the measure, with the owner); or clone how Response's solve gives up (a third approach). Since D34 the stance no longer excludes this option: solver behaviour read from the binary is in) |
| D32 | V alone's shape (A2 part 5, no kernel change). r2c now has the fall of load before the peak, 1.9 % of the peak deep; Response's is 2.2 % and the measure counts a fall from 2 % | decided, owner 2026-11-22 | **Accept as a known deviation for now. No change to the measure.** (The developer had suggested: Accept as a known deviation, or count a fall in r2c's curve where Response has one at the same place and r2c's is within the 5 % target of it (a change to the measure, with the owner). No third approach is proposed: every check at that stage is inside target) |
| D33 | What comes after A2. With D29 to D32 answered as suggested and D30 carried out, the Musts left are −M's two views at its last stage, which follow from how −M ends (a Should, 20 %) | decided, owner 2026-11-22 | **Approved, extended: increment A3**, in this order: D30; the ending of −M with its two Must views; principal tensile stress on M at its last stage (D29); tension's shape (D31); if time allows, the views related to shear. The bounds of D28 apply to each part; an approach that reads the rule from the binary counts as one approach. The parked cases are run once before the end. (The developer had suggested: Next increment: the ending of −M, then the views related to shear (Should). Before phase B, look at the parked cases the changes of A2 moved (Risks)) |


### Left by increment A3 (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D35 | M's last stage (A3 part 3). Response stops a stage's solve once the unbalanced force is within 0.1 % of the loads; r2c goes on to the balanced state. Next to a crack front that difference (0.005 mm/m of strain) is the 7.2 %. With Response's solve switched on, M comes inside (0.4 %) and r2c's last states sit 5 to 20 times closer to Response's; but which side of a crack front a point falls on is then decided by 0.005 mm/m in the other direction on "constant N +200 kN, then M", whose last stage goes from 1.1 to 6.2 %. Seven of eight cases are inside either way; the no-regression bound says the solve stays off | decided, owner 2026-11-22 (suggestion approved) | **Switch Response's solve on**, and accept the last-stage point on "constant N +200 kN, then M" as a known deviation |
| D36 | Tension's shape (A3 part 4). Under a stepped axial strain Response uses another solve: half steps and a wide tolerance, so its states before cracking are 40 to 130 N m out of balance, and that is why it finds one more rising point. With that solve switched on r2c has the point and the shape is inside, but at the peak of tension and of N + M two Must views go outside. In that solve the stiffness it steps on, and the step when moment grows with axial load, are still r2c's own | decided, owner 2026-11-22 | **Leave it off and accept tension's shape as a known deviation** for phase A: matching it is tightening, not scope. The half-built solve stays off; revisit in phase B. (The developer had suggested finishing the solve first.) |
| D37 | What comes next. A3 part 5 (the views related to shear) was not started. One parked case, the I-girder with strands under M, lost its ending to the rupture rule of A3 part 2 (Risks) | decided, owner 2026-11-22 | **Increment A4: the views related to shear first** (the last scope in phase A), with D35 carried out. D36's third step is not in A4. The I-girder's ending waits for phase B. (The developer had suggested D36's third step first.) |

### Left by increment A4 (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D38 | Shear on crack: a line that one program draws and the other does not. Response draws the limit of the shear on a crack only once the largest value on the chart passes 0.001 MPa, and on the negative side only when the negative values are over a fiftieth of the positive. r2c now follows that rule. At two stages the values are so small (0.0015 against 0.0002 MPa; a ratio of exactly a fiftieth at the printed precision) that the two programs fall on either side of the rule, and the measure counts a line that is missing as a difference of 100 % | decided, owner 2026-11-22 (suggestion approved) | **Accept as known deviations** (two stages: M/V = 2 m at cracking, "M constant, then M + V" at its first fall) |
| D39 | How the stirrups remember yielding (A4 part 2c). Response keeps the stirrups' plastic strain at each stage's own points over the depth; r2c keeps it on a fixed grid about 6 mm apart, which is too coarse next to a crack front. With Response's rule switched on, the peak of "N constant, then M + V" comes inside (shear stress 15.5 to 1.3 %) and so do four checks on M/V = 0.5 m, but the rising branch of M/V = 0.5 m, a Must, goes outside (3.7 to 7.6 %): that case has a fall of load and a recovery on the way up, and where r2c takes the fall moves. The no-regression bound says it stays off | decided, owner 2026-11-22 (suggestion approved) | **Leave it off for now**; see whether the same miss appears on the other shapes before taking it up again |
| D40 | Views at the last stage of a shear response. How a shear response ends is a Won't (D1), and the shape check leaves the ending out for shear cases (D25). The views are still compared at the last stage, where the two programs are in different states (often Response's last stage is one it has not converged). Eight of the nine shear cases are outside on their views there, two of them for that alone; so the Should on shear views cannot be met in phase A as it is measured | decided, owner 2026-11-22 (suggestion approved) | **Leave the last stage out of the view checks for shear cases** (a change to the measure, the counterpart of D25), and report the last-stage views separately |
| D41 | What comes next. After A4 every Must miss is a known deviation by the owner's decision, and the Should without shear is met | decided, owner 2026-11-22 | **Neither more Newbeam nor phase B yet: widen the development set step by step**, one variable at a time, so the kernel is not fitted to Newbeam. Step A-1 is shape: the seven Quick Define cases. Each new case meets the same tiers (or its misses become known deviations by the owner's decision); the cases already in the set are held by the no-regression bound. Phase B becomes the review of the test set and targets at the end. Known deviations are watched as the set grows: one that recurs on other shapes is likely Response's solver; one that does not was a Newbeam quirk. (The developer had suggested calling phase A done on its Musts and starting phase B.) |

### Left by step A-1 (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D40a | Reading of D40. Where a shear response ends at its peak, the last stage is the peak. The developer kept that stage in the view checks, as the peak; only a last stage after the peak is left out. (No case in the set ends at its peak in Response today.) | decided, owner 2026-11-22 (reading confirmed) | Yes: a last stage that is also the peak stays assessed |
| D42 | The column with shear is outside on its views at cracking for a reason that is not in the kernel. The two curves agree within 0.4 % up to the peak, stage for stage. The measure reads "cracking" as the first step whose stiffness is under 0.4 of the first; Response's load at one stage is 70.5 kN and r2c's 71.0, and that puts "cracking" at stage 15 of one curve and stage 11 of the other. Since D13 a feature stage is compared with the other curve's stage at the same feature, so the views of stage 15 are compared with those of stage 11: 15 Must and Should views outside, up to 100 %. Compared with r2c's stage 15, none is outside. The same happens at the peak, on a flat top: the largest loads are two stages apart | decided, owner 2026-11-22 (suggestion approved) | **Change the measure:** where the two curves have a stage at the same place (within the target, in load and control value together), compare those; use the feature only where they do not. First part of step A-1b. **Done 2026-11-22**, with D13's purpose kept explicitly: never across a fall of load |
| D43 | **The shape of the I-girder with shear, a Must.** This girder is cambered by its strands and its top is cracked under no load. As the load comes on the top cracks close, at a shear of about 34 kN in Response. Response's curve goes straight from 30.9 to 34.5 kN there. r2c sees the cracks closing as an event between two stages, as Response's rule says, and puts two more stages in between; they are states with the top still cracked, at 49.5 and 51.1 kN, and from them the load falls back to 34.4: a fall of 2.5 % of the peak, where the measure counts from 2 %. Before and after it the two curves agree (rising branch 2.4 %, peak +0.05 %). Why Response puts no stage there was not found: the helper that was reading it was stopped part-way. Its two trial rules (how the program tests "cracked" between stages; a stage put in between that fails is dropped) were not verified, did not remove the fall, and are not in the code | decided, owner 2026-11-22 (suggestion approved) | **Accept as a known deviation for now, and finish the reading** of Response's stage control in step A-1b. **Read 2026-11-22, not resolved:** D48 |
| D44 | Which of the seven have joined the set (`docs/acceptance.md`: a case joins when it meets the criteria or its misses are accepted by the owner) | decided, owner 2026-11-22 | **All seven join the set**, with D42 and D43 as answered |
| D45 | What comes next. Two things were started in step A-1 and not finished: the I-girder with shear's shape (D43), and how Response builds its crack spacing over the depth on other shapes: bars around a circle and hoops (21 and 11 % off on the column), the ends of a stirrup (6 to 8 % on the T-beam), a step in width. The spacing is a Could, but the shear on the crack follows it, and that is the one shear view still outside on the column and the I-girder in Response's own states | decided, owner 2026-11-22 (suggestion approved, reordered) | **Step A-1b before the next variable:** D42's measure change first (it changes what the results page shows), then D43's reading, then the crack spacing from the program. **Done 2026-11-22**; left by it: D46, D47, D48 |

### Left by step A-1b (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D46 | **The longitudinal crack spacing table, read from the program, is switched off.** It reproduces Response's chart to 0.001 mm on every shape tried. Switched on, 43 checks come inside on the 24 cases (measured against the run of record): every longitudinal crack spacing check, crack widths and diagonal spacing with them, the Could views on 20 of 24 cases instead of 15, and the last-stage point of "constant N +200 kN, then M" (D35, a known deviation on a Must: 6.2 to 1.4 %; the Must views would stand at 12 of 13). In Response's own states the column with shear then agrees on every view but one. Seven checks go outside, and one of them is a Must: **the rising branch of M/V = 0.5 m, 2.7 to 9.9 %.** That figure is r2c's last stage. The response of that case ends differently in the two programs (a Won't), r2c's last stage now falls back further than before, and the point it falls to is nearest to Response's fall of load *before* its peak, so the measure counts it with the rising branch. Response's own rising points stay within 2.7 % of r2c's curve. The others that go outside: transverse bond at the peak of the I-girder with shear (2.5 to 49.8 %, which takes that case's Should views outside again) and of M/V = 2 m (3.7 to 22.5 %), both a spike at the end of the stirrups in a stage r2c has not converged (in Response's own state the I-girder's is 0.00 % off); two views of M/V = 0.5 m by a point; the post-peak of V alone (3.7 to 6.9 %). The no-regression bound says a rising branch may not go outside, so the table is off. (The same case was what kept D39 off.) | suggested | **Switch it on, and accept the rising branch of M/V = 0.5 m as a known deviation** of how that response ends. Other options: change the measure so that, for a shear case, r2c's stages after its own peak are not counted with the rising branch (the counterpart of D25, a meta-development change for the owner; it would also settle D39's objection); or leave the table off and carry the 43 checks. Evidence: `docs/kernel.md`, "Crack spacing over the depth"; `python tools/spacing.py RECORD --response-smx` |
| D47 | The column with shear, views at its peak (a Should). Since D42 its views at cracking are inside. At the peak ten Must- and Should-tier views are 8 to 14 % off although curvature and load agree (417.8 against 417.2 kN): the top of this curve is flat within 0.2 % over three stages and the two programs sit in different states on it. Put into Response's own state at that stage, r2c agrees on every such view within 2 % but two: shear on the crack (6.4 %; 1.5 % with D46) and transverse bond (12.5 %, not explained; that rule was never checked on a hoop). This is the known deviation "a peak reached in a slightly different state" of three Newbeam shear cases, recurring | suggested | **Accept as a known deviation**, with the Newbeam ones; look at the transverse bond of a hoop when reinforcement is the variable. Other option: chase the state on the flat top (it is the shear profile iteration, the same part as the parked I-girders' early end) |
| D48 | **The shape of the I-girder with shear (D43) after the reading.** What is now known: at M/V = 2 m Response keeps the stages where the top cracks close (every parked case of this girder), and r2c has them exactly. At M/V = 1 m (this case and one parked one) Response has none of them, and also none where the web cracks later; a third parked case at M/V = 1 m does close in on the web. By every rule read, Response must have tried a stage in between at those places and had it fail; r2c solves the same stage without trouble, with the program's own solve written out as well as with its own. Two approaches were tried (the rules for a stage put in between; the program's solve), and the bound stops a third. What was not read is named in `docs/kernel.md` ("Open: the same girder at M/V = 1 m") | suggested | **Keep it as a known deviation and go on to the next variable (reinforcement).** The fall of load it leaves in r2c's curve is 2.9 % of the peak against the 2 % the measure counts from (2.5 % before this step: r2c now has one more of the stages Response has at M/V = 2 m); peak and rising branch are inside. Take it up again together with the shear profile iteration, which is also what ends the parked I-girders early and what D47 points at: that iteration is the part of the shear solve that has not been set against the program's. Other option: a named third approach now, reading the program's profile update where it reports a stage as not solved (the 3 × 3 solve and its fall-back) |

### The source rule (2026-11-22, after A2)

| # | Question | Status | Answer |
|---|---|---|---|
| D34 | Which source decides how r2c calculates. Until now the thesis was the basis and the binary was read only to answer questions, so every difference between them came to the owner (D21, D22, D30 and others) | decided, owner 2026-11-22 | **The manual decides what exists; the binary decides how it calculates**, including the solver and how a response ends. Where they differ, follow the binary without asking. The thesis guides reading the binary and supplies names and explanation. Exceptions: the owner's overrides only (`docs/acceptance.md`: C2, D12; shear endings stay a Won't, D1). Each rule is written fresh from understanding the routine, not transliterated from decompiled code, and its source recorded in `docs/kernel.md`. In CLAUDE.md and `docs/acceptance.md` |

### The next increment

| # | Question | Status | Answer |
|---|---|---|---|
| D26 | What the first increment on the exit criteria should be | decided, owner 2026-11-22 (suggestion approved, as ranked) | **Increment A2: the Musts without shear, with the measures put right first.** Its parts are ranked below |

The parts of A2, ranked by how much of a Must each closes (the Musts: peak, rising branch,
shape, and the views of the stress state under moment and axial load). Peak is met.

1. **The measures, with the owner** (meta-development). **Done 2026-11-22** (D13, D25, D27,
   D28): shape 15 of 17; the view Must is counted on its own, 2 of 8 inside.
2. **Principal tensile stress at the crack front** (kernel). **Done 2026-11-22:** inside at
   four of five stages; D29 and D30 for the rest.
3. **Steel stress at a crack**, under N + M and under tension. **Done 2026-11-22:** inside.
4. **Tension: the order of cracking and the fall of load.** **Stopped 2026-11-22:** D31.
5. **V alone: the fall of load before the peak. M/V = 0.5 m: the recovery after a fall of
   load.** **2026-11-22:** M/V = 0.5 m inside; V alone investigated, D32.

Also in A2, before part 2: several sections in one file and the horizontal tie are refused
(D23). **Done 2026-11-22.**

Not in A2: the ending of −M (a Should), the views related to shear (Should) and to cracking
(Could), speed.

### Closed by the owner's stance

Settled by "no structural assessment of results" (owner, 2026-11-21) and need no answer: is a
peak after a fall of load the one that matters (Response's largest is used); dm-n1n's failure
mode; whether r2c's states beyond Response's failure are real; Liping LB1 at +1.8 %; findings
H and I (views are now covered by D2).

## Risks

- **Review load.** Development runs faster than the owner can review it. This page is the
  answer: one page per session, not one log per step.
- **Unattended runs** without a scoped GitHub token (setup, not yet done). Branch protection on
  `main` and auto-delete of merged branches are on (owner, 2026-11-22).
- **The set is still narrow.** Three more shapes are in; other reinforcement, material
  models, units and factors are parked. The parked cases are not run on every change, so a
  change that breaks one of them shows only when they are run again.
- **The parked cases moved with step A-1b, again only the I-girder with shear, and on
  balance for the worse** (run once at the end, 2026-11-22; the 50 parked cases r2c
  solves; against the run at the end of step A-1, measured again with the measure of D42
  so that only the kernel differs). Check by check 54 came inside and 64 went outside,
  every one of them on an I-girder case with shear: no parked Newbeam, T-beam or column
  case changed side on any check. On those cases peak is now outside on 8 (6 before),
  rising branch on 9 (6), shape on 12 (10).
  - *The early end has moved from case to case.* Softening model 6 at M/V = 2 m, which
    ended early after step A-1, came back (peak −10.7 to +4.1 %, rising branch 85.8 to
    0.4 %). Models 10, 13 and 7 at M/V = 2 m now end early instead (peak −0.5 to −9.4 %,
    −0.5 to −8.9 %, −0.4 to −6.8 %; rising branch to 75, 75 and 46 %), and model 14's
    rising branch went from 4.9 to 17.9 %. Measured on six of these cases with the two
    changes apart: the stage control rules moved model 7; the transverse crack spacing
    moved the others, in both directions.
  - *What it is:* just after the web cracks r2c cannot settle the shear profile of a
    stage, refuses it because its load is above the largest so far, and steps back until
    it ends; Response keeps a stage there with a lower load. Which case trips over it
    changes with any small change to the kernel. It is the shear profile iteration, the
    one part of the shear solve not yet set against the program's (D48).
  - *Better:* transverse bond came inside on models 11, 12 and 15 (90 to 2 to 5 %).
  - Not looked into further: parked. **But these cases come into the set with the
    material models, and this will be a Must there.**
- **The reading of the stage control stopped short of an answer** (D48). Where it stands,
  routine by routine, is in `docs/kernel.md`; the decompiled routines and traces are
  outside the repository.
- **Part of the crack spacing routines was not read:** they branch on a setting of the
  section that could not be named. The branch taken over fits every chart compared. A
  parked case with another tension stiffening model or factor may take the other branch.
- **A stage control status that the program never returns with shear** is still acted on
  in r2c (it carries on from a solve that has not closed if it is nearly balanced). Found
  while reading the solve; left as it is, because taking it out is a change with no
  check to weigh it by. It is noted in `docs/status.md`.
- **One inferred detail in the new layering:** which side the middle node of the thin layer
  belongs to (the wider one) is taken from Response's charts on one section, not read.
- **Still standing on the parked cases:** I-girder cases with shear outside on peak, rising
  branch or shape; the two cases in US units at M/V = 1 ft outside on rising branch and
  shape; the T-beam at M/V = 2 m on its peak.
- **Speed.** Not worked on. The 24 cases take about two minutes on the owner's machine
  with all of them running at once (measured).
