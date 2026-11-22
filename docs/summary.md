# r2c: the owner's summary

**Read this first.** The one page the owner reads each session: where r2c stands, what
"finished" means, and every decision that is open or has been made. The developer keeps it
current at the end of every session (CLAUDE.md, "Ending a session"). Everything else in
`docs/` is the developer's working record and backs this page; it does not replace it.

Last updated: 2026-11-22, by the developer, at the end of the session that reset the working
set (log 2026-11-22-02). **Four new decisions wait for the owner: D21 to D23 and D26.** D24
and D25 are the developer's readings, to confirm.

## Aim

A really good sectional response calculator, interchangeable with r2x. Completion is judged
against Response-2000 **as documented** (its manual and Bentz's thesis), not against
everything the 1.9.7 binary does. Where the documents and the binary differ, that is put to
the owner (a decision below), not settled by reading the binary. Bells and whistles are built
outside r2c and r2x. (Owner, 2026-11-22.)

## Phases

| Phase | What | State |
|---|---|---|
| **A. Develop the kernel** | Newbeam only, varied in its loads (the 17 cases below). Other sections, reinforcement, material models and units are parked. | **Now.** The working set is reset (2026-11-22: D16, D18, D19 carried out). Next: the first increment on the exit criteria, proposed in D26 |
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
request. Five of them need something that has now been removed, and r2c refuses them.

## Progress against the Phase A exit criteria

On the 17 cases, cases inside target. Measured from the baseline run of 2026-11-22, made
after the reset (`docs/verification-results.md`; the count is a tool's now, not by hand).
**The reset moved nothing**: r2c's results on the 17 are identical, to the last digit, to
those of a run made before it.

| Check | Inside, of 17 | Exit tier (D1, D2) |
|---|---:|---|
| Peak | 17 | Must |
| Rising branch | 16 | Must |
| Shape | 13 (15 once the measure follows D1a; see D25) | Must |
| Post-peak | 10 (7 of the 8 without shear) | Should, without shear |
| Detail views | 1 | Must for stress state under moment and axial load |

What keeps the misses outside:

- *Rising branch:* M/V = 0.5 m (6.1 %), on the recovery after a fall of load.
- *Shape:* M/V = 0.5 m and 2 m differ only in how the response ends, which is a Won't; the
  measure still counts it (D25). V alone: Response has a fall of load before the peak, r2c
  none. Tension: cracking and a fall of load come at one step and are read in a different
  order.
- *Post-peak without shear:* −M, 20 %.
- *Views without shear* (the Must): 7 of the 8 cases are outside. In five it is the
  principal tensile stress chart, mostly by one point; in two the steel stress at a crack.
  Detail in `docs/verification.md`, "Phase A baseline".

Known deviations are in `docs/status.md`: how shear responses end (a Won't, D1), and the
circular column under axial load alone, which is not cloned (D12).

### What was removed (D18)

Each item of the scope inventory is now marked as documented or not, with the manual's page
(`docs/scope.md`). Removed, and now refused as out of scope: draped tendons (D4); the Hsu
softening models combined with Tamai tension stiffening (D5); compression softening 4 (D10),
16 and 17 (later than the manual); a segmental stress-strain curve for reinforcing steel. A
shape with no outline is an input error (D6). Response's program folder was never read, and
is not (D9). Three things were unclear and are kept until the owner decides: D21 to D23.

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
| D20 | `docs/acceptance.md` still says "where r2c and Response differ, Response is right", with no qualifier | decided, owner 2026-11-22 (suggestion approved) | Reworded: "Response as documented is right; undocumented solver behaviour is not cloned"; the tiers of D1 and D2 added as the phase A exit criteria. Done 2026-11-22. |

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
| D17 | Which document defines a complete feature | decided, owner 2026-11-22 (suggestion approved) | The manual (thesis Appendix A) for which features exist; the thesis for how they calculate |
| D18 | Features built beyond the documented set (less common softening models, segmental steel, …) | decided, owner 2026-11-22 | Remove the code |

| D21 | Compression softening models that the manual names but that neither the manual nor the thesis gives a rule for (eleven of them: Vecchio-Collins 1982, 1992-A and 1992-B, Mehlhorn, Maekawa, Noguchi, Belarbi-Hsu, Collins 1978, Kaufmann-Marti, Hsu-Zhang 1998, Hsu 1993). Their rules in r2c were read from the binary. D18 names "less common softening models" for removal; the manual lists them, so they were kept | suggested | Remove them. Keep the four the documents give a rule for or recommend (none, Vecchio-Collins 1986, the CSA rule, Porasz-Collins) and the default (D22). Cost: eleven parked I-girder cases would then be refused. This also disposes of D5 |
| D22 | The default compression softening of Response 1.9.7 (Collins-Bentz 2011) is later than the manual and the thesis, so by D17 it is not documented. Every case uses it. For Newbeam's concrete it is the thesis' own equation; they differ above 57 MPa. The automatic tensile strength is another default where the program differs from the thesis | suggested | Keep. Where a default of Response 1.9.7 differs from the 2000 documents, r2c follows the program, because the oracle runs with its defaults |
| D23 | Two things an input file can carry that the manual does not have, and that r2c reads as the nearest documented thing with no code of their own: several sections in one file (the first is read), and the horizontal tie (read as a stirrup). Both occur only in Response's sample inputs, which are parked | suggested | Leave as they are until phase B, and decide then with the sample inputs in front of us |
| D24 | Reading of "out of scope" and "remove" (D4, D5, D10, D18): r2c refuses such an input and says why, where before it read a drape and ignored it, or ran a Hsu model with Tamai tension stiffening as two independent models | suggested (reading, for the owner to confirm) | Yes: refuse, do not ignore silently |

### Measurement and test set (meta-development)

| # | Question | Status | Answer |
|---|---|---|---|
| D13 | Stage matching: a 0.5 % change in r2c's load can switch the matched stage and flip 11 view checks | decided, owner 2026-11-22 (suggestion approved) | Fix the measure before any work on views |
| D14 | F1: Response's cracking-under-compression rule inside the node | decided, owner 2026-11-22 (suggestion approved) | Yes, after D13 |
| D15 | The generated results JSON is committed on every run (~80,000 lines) | decided, owner 2026-11-22 (suggestion approved) | Build it in CI instead of storing it |
| D16 | The test set has grown to 85 cases | decided, owner 2026-11-22 | Develop on Newbeam; the rest is parked until Phase B |
| D19 | Parked fixtures: delete, or keep and not run by default? | decided, owner 2026-11-22 (suggestion approved) | Keep them, not run by default |

| D25 | The shape check still counts how a shear response ends, against D1a. Two cases (M/V = 0.5 m and 2 m) are outside on shape for that reason alone | suggested (reading, for the owner to confirm) | Change the measure so that shape leaves out the ending for shear cases, in the same piece of work as D13, with the owner |

### The next increment

| # | Question | Status | Answer |
|---|---|---|---|
| D26 | What the first increment on the exit criteria should be | suggested | **Increment A2: the Musts without shear, with the measures put right first.** Its parts are ranked below |

The parts of A2, ranked by how much of a Must each closes (the Musts: peak, rising branch,
shape, and the views of the stress state under moment and axial load). Peak is met.

1. **The measures, with the owner** (meta-development). First, because two Musts are counted
   with them. Stage matching (D13). Shape without the ending for shear cases (D25): shape
   goes from 13 to 15 of 17. The owner sorts the 21 detail views into the three tiers of D2,
   which is a structural judgement; the developer lists them. The report then counts each
   tier and writes the progress table itself.
2. **Principal tensile stress at the crack front** (kernel). Response's rule for cracking
   under compression inside the node (D14), then how closely it spaces its points at the
   crack front. *Views under M and N: five of the seven cases outside.*
3. **Steel stress at a crack**, under N + M and under tension. Not yet investigated.
   *Views under M and N: two of the seven.*
4. **Tension: the order of cracking and the fall of load.** *Shape: one case, the last
   shape miss without shear.*
5. **V alone: the fall of load before the peak. M/V = 0.5 m: the recovery after a fall of
   load.** *Shape: one case. Rising branch: one case, its only miss.* Both are shear cases
   and the cause of neither is known, so this is the least certain part and comes last.

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
- **Unattended runs** without a scoped GitHub token or branch protection on `main` (setup,
  not yet done).
- **Newbeam only** leaves the paths built for steps in width, strands and hoops unexercised
  until Phase B. The parked cases are no longer run on every change, so a change that
  breaks one of them will not show until they are run again; running them on request before
  phase B starts will tell.
