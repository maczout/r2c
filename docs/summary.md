# r2c: the owner's summary

**Read this first.** The one page the owner reads each session: where r2c stands, what
"finished" means, and every decision that is open or has been made. The developer keeps it
current at the end of every session (CLAUDE.md, "Ending a session"). Everything else in
`docs/` is the developer's working record and backs this page; it does not replace it.

Last updated: 2026-11-22, by the developer, at the end of the session on increment A4
(log 2026-11-22-06).

**What changed.** D35 is carried out: r2c now stops a stage's solve where Response stops
it. M's last stage came inside and, as accepted, one point on "constant N +200 kN, then M"
went outside; it is recorded as a known deviation. The views related to shear were worked
on for the first time, from the program: six rules were read and four are in use, 15
checks came inside and 3 went outside, and the nine shear cases are still all outside on
their views. On eight of them that is at least partly because the views are compared at
the last stage, where a shear response ends differently, which is a Won't. A fifth rule
(how the stirrups remember yielding) is written and switched off, because it moves a Must
outside; the sixth (an angle drawn as 180°) was not taken over.

**Three decisions wait for the owner: D38, D39, D40.** D40 is the one that decides whether
the shear views can be met at all in phase A.

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
| **A. Develop the kernel** | Newbeam only, varied in its loads (the 17 cases below). Other sections, reinforcement, material models and units are parked. | **Now.** Increment A4 is done as far as its bounds allow (2026-11-22). Peak and rising branch are met on all 17 cases; shape on 15 and the Must views on 7 of 8, each miss a known deviation by the owner's decision (D32, D35, D36). The Should on shear views is not met: D38 to D40 |
| **B. Validate and refine** | The parked cases come back; the test set and targets are reviewed; r2c is held to them. | Not started. Starts when Phase A meets its exit criteria (D1, D2). |

### The phase A set

Newbeam as Response defines it, in SI units, with no material factors; only the loads
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

Parked until phase B, kept and not run by default (68 cases): other sections (T-beam,
column, I-girder), other materials and reinforcement, units, material factors, More Detail,
no input, and Response's sample inputs. They sit in a folder of their own and can be run on
request. Eleven of them need something that has been removed, and r2c refuses them: five
since the removals of D18, six more (all on Response's sample inputs) since D23.

## Progress against the Phase A exit criteria

Cases inside target, counted by `tools/targets.py --counts` from the run of 2026-11-22 made
at the end of A4 (`docs/verification-results.md`). "Before" is the run of record of A3.

| Check | Before | Now | Exit tier (D1, D2, D27) |
|---|---:|---:|---|
| Peak | 17 of 17 | 17 of 17 | Must: met |
| Rising branch | 17 of 17 | 17 of 17 | Must: met |
| Shape | 15 of 17 | 15 of 17 | Must (a shear case's ending left out: D25). The two misses are known deviations (D32, D36) |
| Views of the stress state, without shear | 7 of 8 | 7 of 8 (M came in, "constant N +200 kN, then M" went out) | Must. The miss is a known deviation (D35) |
| Post-peak | 12 of 17 | 12 of 17 (all 8 without shear) | Should, without shear: met |
| Views related to shear, and stress-state views with shear | 8 of 17 | 8 of 17 (none of the 9 with shear) | Should |
| Views related to cracking | 8 of 17 | 8 of 17 | Could |

Check by check over all 17 cases, 16 came inside target and 4 went outside.

### Increment A4, part by part

| Part | What was done | Outcome |
|---|---|---|
| 1. D35 | Response's solve of a stage under a stepped curvature (it stops once the unbalanced force is within 0.1 % of the loads) is switched on | **As the owner accepted.** M's last stage 7.2 to 0.4 %; "constant N +200 kN, then M" at its last stage 1.1 to 6.2 %, recorded as a known deviation. Nothing else moved |
| 2a. The limit on concrete tension above the cracked zone | Read from the program: between the flexural tension zones the longitudinal steel's limit is three times the tensile strength. r2c had none there | **In use.** 11 checks came inside (nine at diagonal cracking on "N + M + V together"), none went outside |
| 2b. Three shear charts as the program draws them | The grey envelope behind the strain charts (each stage has its own, from the stage it followed); shear on crack with its sign and its limit lines; transverse bond (an average over five stirrup diameters) | **In use.** 4 checks came inside; 3 went outside: two where one program draws a limit line and the other does not, at stresses of about 0.001 MPa (D38), one bond check at a peak the two programs reach in slightly different states |
| 2c. How the stirrups remember yielding | Read from the program: the plastic strain is kept at each stage's own points over the depth; r2c keeps it on a coarse fixed grid | **Stopped, switched off.** It fixes the peak of "N constant, then M + V" (shear stress 15.5 to 1.3 %), but the rising branch of M/V = 0.5 m goes outside (3.7 to 7.6 %), a Must. Two variants, same result. D39 |
| 2d. An angle drawn as 180° | Read from the program; depends on the order in which Response makes its points over the depth, which r2c does not keep | **Not taken over.** Two points at the peak of M/V = 2 m |

**Why the nine shear cases are still outside on their views.** Eight of them are outside at
the last stage, where r2c's response and Response's end in different states (how a shear
response ends is a Won't, D1); two of the eight are outside for that alone (M/V = 1 m, V
with constant compression). At the other stages the misses left are: a peak reached in a
slightly different state (three cases), the known deviations of the curve on M/V = 0.5 m,
M/V = 2 m and V alone, and one stage neither program has converged. Put in Response's own
states, r2c draws its shear views within target at every stage but three
(`docs/verification.md`, "A4").

Every rule taken over is in `docs/kernel.md` with its source. Increment A3 is in the log
of 2026-11-22-05.

Known deviations are in `docs/status.md`: how shear responses end (a Won't, D1), the
circular column under axial load alone, which is not cloned (D12), the fall of load
before the peak under V alone (D32), tension's shape (D36), and the last-stage point on
"constant N +200 kN, then M" (D35).

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
| D16 | The test set has grown to 85 cases | decided, owner 2026-11-22 | Develop on Newbeam; the rest is parked until Phase B |
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
| D38 | Shear on crack: a line that one program draws and the other does not. Response draws the limit of the shear on a crack only once the largest value on the chart passes 0.001 MPa, and on the negative side only when the negative values are over a fiftieth of the positive. r2c now follows that rule. At two stages the values are so small (0.0015 against 0.0002 MPa; a ratio of exactly a fiftieth at the printed precision) that the two programs fall on either side of the rule, and the measure counts a line that is missing as a difference of 100 % | suggested | **Accept as known deviations** (two stages: M/V = 2 m at cracking, "M constant, then M + V" at its first fall). The rule is the program's (D34). Other options: have the measure leave out a line that only one program draws when the values that decide it are within the printed precision (a change to the measure, with the owner); or go back to drawing both limit lines always, which is not what the program does |
| D39 | How the stirrups remember yielding (A4 part 2c). Response keeps the stirrups' plastic strain at each stage's own points over the depth; r2c keeps it on a fixed grid about 6 mm apart, which is too coarse next to a crack front. With Response's rule switched on, the peak of "N constant, then M + V" comes inside (shear stress 15.5 to 1.3 %) and so do four checks on M/V = 0.5 m, but the rising branch of M/V = 0.5 m, a Must, goes outside (3.7 to 7.6 %): that case has a fall of load and a recovery on the way up, and where r2c takes the fall moves. The no-regression bound says it stays off | suggested | **Leave it off for phase A** and take it up with the recovery after a fall of load on M/V = 0.5 m (the case was at 6.1 % before A2 and is sensitive to everything). Other options: switch it on as the program's method (D34) and accept the rising branch of M/V = 0.5 m as a known deviation (it was one before A2); or a third approach, named: put r2c in Response's states stage by stage through that fall of load to find which of the two programs' stages differs first |
| D40 | Views at the last stage of a shear response. How a shear response ends is a Won't (D1), and the shape check leaves the ending out for shear cases (D25). The views are still compared at the last stage, where the two programs are in different states (often Response's last stage is one it has not converged). Eight of the nine shear cases are outside on their views there, two of them for that alone; so the Should on shear views cannot be met in phase A as it is measured | suggested | **Leave the last stage out of the view checks for shear cases** (a change to the measure, for the owner; the counterpart of D25), and report the last-stage views separately as before. With that, 2 of the 9 shear cases would be inside on their views today (measured: `tools/viewmisses.py --no-endings`). Other options: keep the measure and accept that the shear views stay a Should not met in phase A; or lift the Won't on shear endings (a larger piece of work) |
| D41 | What comes next. After A4 every Must miss is a known deviation by the owner's decision, and the Should without shear is met | suggested | **Decide D40 first**, since it says what is left of phase A. Then either an increment A5 on what the shear views still miss away from the endings (the stirrups' memory with the fall of load on M/V = 0.5 m, D39; the calculated shear stress after a fall of load), or call phase A done on its Musts and start phase B, where the parked cases come back (Risks) |

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
- **Newbeam only** leaves the paths built for steps in width, strands and hoops unexercised
  until Phase B. The parked cases are no longer run on every change, so a change that
  breaks one of them will not show until they are run again.
- **The parked cases moved with A4** (run once at the end, 2026-11-22, against the run made
  at the end of A3; the 57 cases r2c solves). Check by check 41 came inside and 23 went
  outside.
  - *Better:* **the I-girder with strands under M is back inside after the peak (18.8 to
    0.0 %)**, the case A3 had put outside; so is Newbeam with linear concrete under M (6.4
    to 0.3 %). Both through Response's solve (D35).
  - *Worse on peak, rising branch or shape, one case:* the I-girder with softening model
    11 at M/V = 1 m, rising branch 4.0 to 6.3 %.
  - *Worse on a view:* transverse bond went outside on five parked cases; far on one,
    Newbeam with stirrups over part of the depth (2.5 to 55.6 %). The bond rule was read
    and checked with stirrups over the whole depth only. One I-girder case at M/V = 2 m
    (softening model 1) lost eight view checks at cracking and at its last stage.
  - Not looked into: parked. The stirrups over part of the depth is the first thing to
    look at when that case comes back.
- **Still standing on the parked cases:** I-girder cases with shear outside on peak, rising
  branch or shape (one far: Kaufmann-Marti softening, peak −8 %). The one parked
  regression test that failed by a hair after A2 (linear concrete) passes again.
- **Speed.** Building the layers again for each state costs time: the 17 cases together
  take about a third longer (345 to 470 s of computing, measured on one machine). Speed was
  not in A2.
