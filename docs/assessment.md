# The independent assessment at the finish, with the developer's answers

The brief's finishing steps (`docs/brief.md`, "Finishing"; the owner, 2026-11-26): an
independent assessor, given only the evidence and the brief, first checks the rule that
tells where Response's solve gives up, then explains the largest misses on both held-out
sets. The assessor was a separate agent that had seen nothing of the development: not the
repository's documents, logs or source, only a folder of records outside the repository
(both held-out sets opened case by case, the two programs' records, Response against
itself, traces of Response's own stage control, the measures) and the brief. It ran
neither program.

**Its findings are below as it wrote them**, whole and in its order. Two things only were
changed: the folder paths of the machine are written `EVIDENCE/` and `WORK/`, and after
each finding the developer's answer is set in, marked as such. The developer's own
readings (`tools/sources.py` and `tools/uncut.py` on the scorer's runs, a trace of r2c on
one development case) were made before or beside the assessor's and not shown to it.
Case names beginning `h-` and `f-` are the first and second held-out set's; what each is
is in `heldout/manifest.json` and `heldout/finish-manifest.json`.

---

# Independent assessment of r2c against Response-2000 (finish, 2026-11-27)

Made from `EVIDENCE/` alone. Nothing else on the machine was read; r2c and
Response were not run. My scripts are in `WORK/` (`cutdep.py`,
`ends.py`, `traces.py`, `beyond.py`, `miss.py`, `allmiss.py`, `overlap.py`, `margins.py`); every number
below comes from one of them or from the evidence file named. "First set" is the 55 held-out cases,
"second set" the 22. "Raised" is Response with every concrete strength raised by 0.05 %.

**In one paragraph.** The rule identifies the right cases: on the held-out sets it fires on 15 cases,
and in the 14 whose trace is complete Response's tries did run out. But the rule, with the owner's cut,
is what carries the shear priority 1 score: without the cut it is 22 of 28 (first set) and 11 of 12
(second), not 28 of 28 and 12 of 12, because on six cases r2c's whole response peaks 5 to 32 % above
Response's (a seventh turns on an artefact of the measure). In 12 of the 15 cases r2c's own copy of Response's solve does not give up where Response
did. There is no priority 1 miss on either set as measured; all 37 view checks outside target are
shear cases, 36 of them at the peak stage, and about three quarters are real differences that
Response's own scatter does not explain.

## Task 1: the rule

**R1. On the held-out sets the rule fires only where Response's tries ran out, as far as the traces
show; one of the 15 cases cannot be confirmed.**
The rule fires on 10 first-set and 5 second-set cases (`gaveup-first.txt`, `gaveup-second.txt`). In 14
of them the trace ends with one to twelve failed tries after the last kept stage, the last at a step
multiplier of 0.006 or 0.008, each marked "no solve" (`traces.py` over `traces/held-out/*.txt`). The
15th, h-heavy-negmv, has a trace that stops unfinished at 29 stages where the capture has 35, so it
shows nothing about the end; its curve has the same pattern as h-fc70-m2v and h-se100-m25v (R5).
Confidence: high for the 14, low for h-heavy-negmv. A complete trace of that case would settle it.

> **The developer's answer (R1).** Agreed. The trace of that one case stopped early because running Response under the debugger changes its timing; it was not made again.

**R2. In the development set the rule fires on one traced case where Response did not give up, and
the 0.8 condition is not what tells the two endings apart.**
newbeam-v0-m: the rule cuts it (last stage at 0.922 of peak), but the trace has no failed try after the
last kept stage; that stage was kept with a profile error of 160.55 % and state code 3. Response ended
of its own accord. The first-set case h-stheavy-m3v ends the same way (0.930 of peak; its last four
kept stages carry code 3 and errors of 49 to 91 %; no failed try) and escapes the rule only because
r2c happened to end within 5 % of the same place. So "at least 0.8 of the peak, therefore its tries
ran out" (`measures.md`) is false in two traced cases. The other seven traced development cases on
which it fires do end in failed tries. Effect on verdicts: priority 4 only, on newbeam-v0-m (ending
0.7 % cut, 5.9 % uncut, `cutdep.py`); none on a held-out case.
Confidence: high. What code 3 means is not in the evidence.

> **The developer's answer (R2).** Agreed, and it is a fault in the developer's rule: a last stage at 0.8 of the peak or more is necessary for a give-up, not proof of one. On the development case named, Response ended on a kept stage of its own and the case should not be cut. Correcting it changes a measure, which is the owner's to allow (`docs/summary.md`, "Needed from the owner"); nothing was changed. Its effect is on the ending of that one development case; no held-out verdict turns on it.

**R3. In two held-out cases the first tries Response refused after its last stage were solved states
refused on a state code, not failures to solve; the claim in `measures.md` that r2c "would end there
too" is not borne out there.**
h-marshall-m2v: after the last kept stage, a try "code 3 above" at load 1.00 of the largest with a
profile error of 0.79 %. f-st200-m2v: "code 3 above" (0.82 %), then "code 3" (1.04 %). Only after
those do the "no solve" tries run down to the smallest step. The same appears in development
(newbeam-heavy2500-negm2v, tbeam-negm4v). r2c goes on past that point to a peak 5.1 % and 3.5 % higher
(`cutdep.py`). If code 3 is one of Response's limits, r2c does not stop on it in these cases.
Confidence: medium that this matters; I cannot tell from the evidence what code 3 is. The meaning of
the state codes, and whether r2c's states just past the cut carry the same code, would settle it.

> **The developer's answer (R3).** Agreed that the measure's sentence is not borne out, and the cause is not found. What the codes are (`docs/kernel.md`, "The state code"): 3 is the web crushing, 4 a transverse strain beyond the stirrups' rupture strain; "code 3 above" is Response refusing a stage whose web is crushing while the load is above the largest so far. So on these cases Response's response ends because it finds the web crushing with the load still rising, refuses the stage, and then cannot solve a smaller step; that is not simply a solve that gives up. The developer traced r2c on the development case of this kind the assessor names (the T-beam under negative moment at M/V = 4 m; `python tools/trace.py`, *measured*, 2026-11-27): at the curvature of Response's refused try r2c's stage settles in four passes with state code 0 and is kept, and r2c goes on. The rule written and off that tests the code on every pass (`Shear.pass_code`) was tried on that case and changes nothing: r2c's state there does not crush the web at any pass. Why Response's state does and r2c's does not, at the same curvature and load, is open. Whether a case that ends this way falls under the override is put to the owner.

**R4. The rule misses no held-out case that matters.**
Nine held-out cases have failed tries at the end of the trace and no cut: h-ft-mv, h-liping-nmv,
h-nb-m100-v, h-nb-m3v, h-shrink6-mv, h-tb-negm2v, f-ig-m25v, f-liping-m3v, f-mid500-m15v. In each r2c
ends within the 5 % of Response's last stage (r2c's last point at 0.954 to 1.021 of Response's largest
control value and 0.967 to 1.002 of its peak load, `ends.py`), so r2c did not carry on in any sense
that changes a result; all nine are inside on priority 4 or have no such check. The traced cases
whose load had fallen (h-fc25-mv, h-slab-mv, f-fy350-mv) show no failed tries: the last stage was
kept with an error of 88 to 147 % and code 4.
Confidence: high for the traced cases. Twelve held-out shear cases under 0.8 were not traced.

> **The developer's answer (R4).** Agreed.

**R5. Priority 1 with shear depends on the cut on 6 of 28 first-set cases and 1 of 12 second-set
cases; priority 4 on 9 and 5; priorities 2 and 3 on none.**
`cutdep.py` recomputes every comparison with `carried_on` switched off (and reproduces the stored
comparisons with it on: 0 mismatches). Shear totals with the rule / without:

| Set | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| First | 28 / 22 of 28 | 16 / 16 | 25 / 25 | 20 / 11 of 27 |
| Second | 12 / 11 of 12 | 7 / 7 | 12 / 12 | 9 / 4 of 12 |
| Development | 73 / 67 of 78 | 47 / 47 | 69 / 69 | 51 of 77 / 28 of 75 |

The peak of r2c's whole curve against Response's, in the cases whose priority 1 verdict turns:
h-fc70-m2v +31.6 %, h-heavy-negmv +27.2 %, h-se100-m25v +15.5 %, h-tb-m3v +8.9 %, h-marshall-m2v
+5.1 %, f-tb-m15v +5.4 %. The seventh, h-fc90-mv, turns on the rising-branch check (83.2 %) only
because r2c's final collapsed point is measured against the rising branch; its peak differs by 0.3 %.
Under the cut all are within 0.2 %. The threshold for shear priority 1 is 93.4 %: r2c meets it with
the rule (100 %) and not without it (78.6 %). The view checks do not change with the cut at all.
Confidence: high (arithmetic on the records).

> **The developer's answer (R5).** Agreed; counted again by the developer with a tool of its own and the numbers are the same (`python tools/uncut.py`, *measured*, 2026-11-27). The cut is the owner's override of 2026-11-25 applied as decided, but its size had not been shown beside the totals before. The sign-off page now gives priority 1 with shear both ways, and the README says by how much r2c's peak can stand above Response's.

**R6. Beyond Response's last stage r2c does two different things, and neither is a smooth
continuation that Response merely failed to compute.**
(a) A jump, 3 first-set cases. Both programs sit on a plateau with steps of 0.001 to 0.005 in shear
strain, then r2c's next stage is somewhere else (`beyond.py`): h-fc70-m2v, shear 124.96 to 142.16 with
shear strain falling from 2.696 to 1.68 and curvature rising from 5.05 to 8.06; h-heavy-negmv, 142.11
to 160.01; h-se100-m25v, 362.2 to 404.3. r2c then climbs to 167.3, 183.7 and 418.3. Response's own
failed tries were heading the same way: for h-se100-m25v they read 404.87 and 405.49 with profile
errors of 11.6 % and 22.8 %; for h-fc70-m2v 154.84 at 35.5 %. In these three r2c's `carried_from`
(43, 36, 42) is one stage past Response's stage count (42, 35, 41): r2c reproduces the give-up and
then the override takes over, as the owner decided. Response does not converge on that upper branch;
whether r2c's states on it are converged the records do not say.
(b) A rising path that Response does not find, 12 cases. r2c's own copy of Response's solve gives up
5 to 46 stages after the point of Response's last stage, or only at r2c's own end (h-deep-m2v 83 against 68 stages, h-ig-m4v 99 / 71,
h-marshall-m2v 88 / 70, h-st100-mv 149 / 108, h-tb-csa-mv 72 / 51, h-tb-m3v 84 / 54, h-fc90-mv 94 / 91,
f-csoft8-m2v 88 / 126 at a different stage spacing, f-deep800-m25v, f-fc60-m15v, f-st200-m2v,
f-tb-m15v). So there r2c "carrying on" is not the override acting at Response's give-up; r2c simply
solves stages where Response could not. Response's failed tries in these are mostly not near misses:
state code 4, load at 2 to 13 % of the largest, profile errors of 60 to 2400 %. A kept stage with code
4 and a large error is how Response's fallen-load endings look (R4). r2c's load beyond rises by up to
8.9 % (not at all in h-tb-csa-mv, which is past its peak).
Confidence: high on what the records show; low on which program is right in (b). It would take the
meaning of code 4 and r2c's state at its first stage past the cut, set beside Response's failed try.

> **The developer's answer (R6).** Agreed on both kinds. (a) is the override at work as written. (b) is not: there r2c's copy of Response's solve does not fail where Response's does, so r2c carries on without the override acting; the measure cannot tell the two apart and cuts both. It is the known deviation on stages that do not settle, seen at the end of a response, and R3's unexplained difference is part of it. Response's failed tries with code 4 are states run away past the stirrups' rupture strain. Whether r2c's states beyond Response's last stage are right was not checked against anything but r2c's own solve: r2c's stages there are settled by its own measure (profile error under 1 % on the case traced under R3), and that is all that can be said. `docs/deviations.md` now describes (b) as an open difference.

**R7. Response's give-up point is mostly repeatable, so in most of these cases it is a property of
Response's result, not scatter.**
Raised against Response as it is (`ends.py`): in all 10 first-set cut cases the raised run ends within
2.5 % of the same place (0.992 to 1.025 of the largest control value), though sometimes with another
number of stages (h-deep-m2v 84 against 68). In the second set three of five do; f-deep800-m25v ends at
0.845 and f-tb-m15v at 0.864. Elsewhere it moves a lot: h-nb-m3v ends at 0.666, and f-fy350-mv changes
kind (0.247 of peak as it is, 0.982 raised). So an engineer running Response on h-fc70-m2v gets a
peak shear of about 127 kN every time (its last stage, 125.0, is 0.983 of it); r2c reports 167.3 kN.
Confidence: high for this one perturbation; other perturbations are not in the evidence.

> **The developer's answer (R7).** Agreed, and it is what a user most needs to know: where the two differ here, Response's lower figure is its repeatable answer. In the README's known limitations.

**R8. Applying the rule to Response against itself changes nothing, but that comparison is hit by
the same phenomenon in the direction the rule does not cover.**
The rule fires on no raised case in either set; the totals with and without it are identical
(`cutdep.py`). The three shear priority 1 failures of Response against itself are all the raised run
ending short: h-nb-m3v (rising branch 32.3 %), f-deep800-m25v (15.4 %), f-tb-m15v (13.6 %)
(`opened/*-response-against-itself.md`). A run that stops short is counted outside for r2c as well,
so the treatment is the same. The consequence is only that the thresholds contain some of Response's
ending scatter: h-nb-m3v alone accounts for one of Response's failures on each of priorities 1, 2
and 3 in the first set.
Confidence: high.

> **The developer's answer (R8).** Agreed.

**R9. Verdict: sound as a way of finding the cases, with three reservations; what needs the owner's
eye is the size of what the cut sets aside.**
The conditions "same place within 5 %" and "ends apart" do no work in r2c's favour on the held-out
sets: every cut case passes Response's last stage within 0.2 % (column "off"), and no case is cut
that ends near Response's end. Reservations: (1) the 0.8 condition does not establish a give-up (R2);
(2) the records cannot tell a give-up from a state refused on a code (R3); (3) the rule cannot tell
the override at work from r2c not reproducing Response's failure to solve (R6b). What I would change:
- report shear priority 1 both ways in the summary (28 and 22 of 28; 12 and 11 of 12), with the six
  peak differences of R5 listed as a known deviation;
- have r2c mark in its record the stage at which Response's response ends, so a user can read off
  Response's peak; today its header gives `peak-stage` 79 for h-fc70-m2v where Response's is 28;
- treat (b) of R6 as an open difference between the programs, not as the override;
- where a trace exists, let it decide; newbeam-v0-m should not be cut.

> **The developer's answer (R9).** Taken up: priority 1 with shear is reported both ways (first suggestion) and (b) of R6 is listed as an open difference (third). Put to the owner, since neither is the developer's to decide in an increment without kernel changes: a line in r2c's record that marks the stage where Response's own solve gave up (r2c knows it in the cases of kind (a); it is a change to the record, which is r2x's format), and a correction to the rule so that a case like the one in R2 is not cut (a change to a measure).

## Task 2: the largest misses

There is no priority 1 miss on either set as measured. Without shear every check is far inside: peak
within 0.01 %, curves within 0.06 %, the largest view difference 4.5 % (h-ig-negm) in the first set and
0.54 % in the second (`margins.py`). With shear, under the cut, the peak is within 0.5 % and the rising
branch within 1.43 % on every case. `allmiss.py` lists all 37 view checks outside target: 31 in the
first set over 13 cases, 6 in the second over 5 cases; all shear; 36 at Response's peak stage, 1 at a
fall; 20 at Response's very last stage and 10 more within two stages of it. On 28 of the 37 the raised
run is inside target on the same check, so Response's own scatter does not explain them.

**M1. h-tb-csa-mv, reinforcement stress at a crack, 100 %: the same state, a different view, only
with material factors.**
At stage 37 every other view agrees to 0.0 % (1.5 % for one), and the raised run agrees to 0.0 %.
Response prints 0 for the two tension layers (whose average stress is 382.5, the factored yield) and
-69.38 for the top bar; r2c prints 382.5 for the tension layers and 0 for the top bar. The case has
factors 0.65, 0.85, 0.90; the same miss is in development (tbeam-csa-m2v, 100 %). A real, repeatable
difference in one view; it does not touch the state or the strength.
Confidence: high on what differs; I cannot tell which print is the intended one.

> **The developer's answer (M1).** Agreed; a known deviation (`docs/deviations.md`): the binary's routine for the stress at a crack leaves early there and shows the yielded bars no value. Put into Response's state r2c differs by the same 100 % (`python tools/sources.py`), so it is a rule, read and not written.

**M2. h-ig-m4v, shear on crack 46.8 % and seven other checks: part a different state, part a spike
at the flange-web junction that r2c does not have.**
Stage 70 is Response's last stage and its peak, of a response it abandoned (nine failed tries). r2c
has no stage there: its stages 64 and 65 lie either side and stage 65 is compared, 2.44 % further in
curvature, with a largest shear strain of 25.53 against 24.18. That accounts for the 5.2 to 5.7 %
on the three strain views. The large numbers are local: at depths 379 to 381 mm Response's shear on
crack is 0, 2.881, 1.67, 0.91; r2c's is 0.47, 0.39, 0.38, 0.37. The principal tensile stress there is
1.88 and 2.23 in Response and 0.08 in r2c: r2c has two more layers cracked. Response is not steady at
that point either: the raised run gives 4.398 where Response has 0 and scores 0.3 %, because the
measure forgives a spike that moves by one layer, and it is itself outside on the principal tensile
stress (7.5 %).
Confidence: medium. A stage of r2c at Response's curvature would separate the two parts.

> **The developer's answer (M2).** Agreed in the main. Put into Response's own state at that stage r2c is within 2 % on seven of the eight views, shear on the crack included (0.2 %), and still 6.8 % out on the principal tensile stress (`python tools/sources.py`, *measured*): so the state for most of it, and one view at the junction that the state does not explain.

**M3. Transverse average bond: nine cases, r2c lower than Response where the view is largest; the
most frequent miss.**
h-nb-m100-v 27.9 % and 7.5 %, f-fc60-m15v 20.5 %, f-st200-m2v 12.2 %, h-marshall-m2v 9.9 %, h-ig-m4v
9.6 %, f-col-n1500-m15v 9.1 %, h-liping-nmv 8.3 %, h-stheavy-m3v 5.5 %, f-nb-m150-v 5.5 %; the only
miss in six of them. The state is the same where I looked (f-fc60-m15v: every other view within
1.7 %, strains within 0.4 %; h-marshall-m2v and h-liping-nmv matched within 0.11 %), and the values
differ over a few points near the bottom of the stirrups: 34.69 against 22.89, 25.85 against 23.29,
29.48 against 27.03, 18.58 against 9.75. Response is steadier than that in most (raised 0.0 to 4.7 %
in eight of the ten checks) but outside target itself in f-fc60-m15v (6.0 %) and at the fall in
h-nb-m100-v (5.8 %), and far outside on this view elsewhere (48.5 % f-ig-m25v, 68.3 % h-ig-dep4-m3v).
A same-state difference in one derived view, r2c the lower in the four cases I opened.
Confidence: medium-high that it is a view difference; the cause is not visible in the records.

> **The developer's answer (M3).** Partly different. The developer's measure of the same ten checks, with r2c put into Response's own state at the stage (`python tools/sources.py`, *measured*): five come inside (2 to 4 %: Newbeam under a moment then shear at its peak, Newbeam with 60 MPa concrete, the Marshall sample, the I-girder, Newbeam under 150 kN m then shear) and five stay outside (6 to 16 %: the Liping sample under compression, Newbeam with heavy closed stirrups, Newbeam with stirrups at 200 mm, the column under compression, and the fall of load of Newbeam under a moment then shear). So about half is a rule of this chart near the bottom of the stirrups that r2c does not have, as the assessor reads it, and half is the state: the chart is a difference of the stirrups' stress between neighbouring nodes and moves by more than the strains do. The rule was not looked for on the development set, where the same chart was read as the state.

**M4. f-liping-m3v, principal tensile stress 26.7 % and shear stress 8.3 %: one or two points at a
change of width; Response is exactly repeatable there.**
Response's last stage (72), abandoned after two failed tries. r2c's stage is 1.07 % earlier in
curvature and every strain view is within 2.6 %. At depth 207 mm Response has 0.82, 2.225, 1.06 down
the profile and r2c 1.54, 1.41, 1.04; the shear stress there is 1.745 against 1.268. The raised run
agrees with Response to 0.0 % on both. The absolute difference is 0.68 MPa on a chart whose largest
value is 2.55, over a band of less than 1 mm.
Confidence: high that it is local and real; low on the cause.

> **The developer's answer (M4).** The developer's measure reads it as the state: put into Response's own state r2c is within 2.6 % and 1.5 % on the two views (`python tools/sources.py`). The assessor finds the strains within 2.6 % and the difference over less than a millimetre at the change of width; both can hold, since the node at a step in width is where the two programs' profiles of shear strain differ. Not settled.

**M5. h-se100-m25v, shear stress 11.4 %: the same state, a different shear stress just below a change
of width.**
Stage 39, on the plateau where Response's step had shrunk to 0.008 before it gave up. Strains agree
within 0.2 %; the raised run within 1.2 %. From depth 330 mm down Response has 0.746, 1.014, 1.115,
1.165 and r2c 1.017, 1.179, 1.247, 1.284, over seven points, on a chart whose largest value is 1.637.
h-tb-m3v (shear stress 7.1 %, shear on crack 8.5 %) and h-deep-m2v (shear stress 5.7 %) are single
points of the same kind at 372.5 mm and 406.7 mm; in h-tb-m3v Response has a one-point value of 3.635
that the raised run repeats (3.646) and r2c has 0.
Confidence: high that these are same-state view differences confined to a junction.

> **The developer's answer (M5).** As M4: in Response's own state r2c is within 0.3 % (the se100 sample), 1.0 % and 0.6 % (the T-beam) and 0.5 % (the deep beam) on these views, so the developer reads the state at the layers of the junction, not the view's rule. What the assessor shows is that the strains printed agree to 0.2 % all the same; the profile of shear strain across a step in width is the place to look (`docs/kernel.md`, "At a step in width").

**M6. h-nb-m100-v, six checks at the last stage: Response's own stage there is not settled.**
Stage 52 is the last stage and the peak; the trace shows it kept after 16 passes with a profile error
of 2.94 % (stage 51: 1.73 %; a stage normally settles under 1 %), followed by eleven failed tries. r2c
ended there too. Curvature agrees within 0.25 %, but r2c's largest shear strain is 16.10 against
16.46 and the transverse strain 20.74 against 21.04, hence 5.4 to 6.3 % on four views; the bond is M3.
The raised run is inside target on all five checks (1.2 to 3.4 %).
Confidence: medium; r2c is close to an unsettled stage of Response, but Response repeats it.

> **The developer's answer (M6).** Agreed. In Response's own state r2c is within 0.3 % on the four views and 2.5 % on the bond.

**M7. h-nb-ncomp-mv (four checks to 9.1 %) and h-shrink6-mv (two to 8.2 %): r2c is nearer to Response
than Response is to itself.**
Raised gives 12.9, 16.4, 13.5 and 12.7 % where r2c gives 6.4, 9.1, 6.9 and 6.3 %; and 14.6 and 14.3 %
where r2c gives 8.2 and 7.8 %. In h-shrink6-mv the difference is one point at depth -248 mm (2.716
Response, 4.384 r2c, 1.043 raised). Neither is evidence against r2c. h-nb-ncomp-mv is of the kind the
owner left outside (axial compression and shear).
Confidence: high.

> **The developer's answer (M7).** Agreed.

**M8. h-stheavy-m3v (7.2 %, 8.9 %, 5.5 %): r2c has no stage where Response has its peak.**
Response's stage 61 (curvature 43.81) is an extra stage at a halved step. r2c's stages 60 and 61 match
Response's 60 and 62: the bar stresses are 451.11 and -400.0 in r2c's stage 61 against 451.126 and
-400.0 in Response's stage 62. The check compares Response's 61 with r2c's 60, 3.47 % earlier, where
the compression bar is at -343.8 against -376.2. A difference of stage sequence, not of the
calculation; the peak differs by 0.09 %.
Confidence: high.

> **The developer's answer (M8).** Agreed: a stage that Response has and r2c does not.

**M9. h-slab-mv, principal tensile stress 9.0 %: the crack front sits a few layers differently.**
At depth 56 mm r2c has the uncracked value 1.89 over four points where Response has 1.06 to 1.82; r2c's
stage is 0.87 % earlier in curvature and 0.50 % lower in load. Response repeats itself to 0.1 %, though
its own neighbouring stages differ by 50.2 % on this view: the front is moving fast at the peak of a
member without stirrups.
Confidence: medium. I cannot tell whether the earlier stage explains all of it.

> **The developer's answer (M9).** Agreed; in Response's own state r2c is within 0.1 %.

**M10. Endings (priority 4, reported only): r2c runs on where Response stops, and ends at the peak
where Response records a collapse.**
f-cm4-n300-m25v (464 %) and h-cm4-m2v (52.9 %): r2c follows Response's falling steps (26.5, 411.9;
34.6, 264.6; 43, 196.7 against Response's 26, 411.6; 35.1, 264.9; 42.9, 196.6), then runs on to a
control value of 295 where Response and the raised run both stop at 52. The other kind: in 11 cases
Response's last stage is a collapsed one at 0.05 to 0.58 of the peak and r2c's is at 0.96 to 1.00
(`margins.py`). Seven are counted outside (5.7 to 22.3 %); four are counted inside (h-col-n2000-mv,
h-dmn1n-m3v, h-ig-dep4-m3v, f-col-n1500-m15v) because Response's collapsed point happens to lie near
r2c's rising branch. Nothing before the peak is affected.
Confidence: high.

> **The developer's answer (M10).** Agreed. Endings with shear are the lowest priority and were not worked on; the four counted inside by where Response's collapsed point happens to lie are a weakness of the ending measure, noted for the owner with R2.

## On the scores as a measure

**S1. The totals agree with what I count.**
Recomputing every comparison from the records gives, for r2c: first set 27, 27, 27 of 27 without shear
and 28, 16, 25 of 28 and 20 of 27 with; second set 10, 10, 10 of 10 and 12, 7, 12, 9 of 12. For
Response against itself: 20, 27, 27 of 27 and 27, 18, 25 of 28 and 25 of 27; second set 7, 10, 9 of 10
and 10, 5, 8 of 12 and 9 of 10. These equal `totals.json` (increment 8), `finish-totals.json`,
`repeatability.json`, `finish-repeatability.json` and the tables in `opened/`. All 154 capture hashes
in the two manifests match the records (`margins.py`).
Confidence: high.

> **The developer's answer (S1).** Noted.

**S2. The duplicate f-ig-m25v does not change the picture; the sets are less independent of the
development set than "sections not tuned against" suggests.**
f-ig-m25v is the only held-out case with the same input, loading and factors as a development case
(`overlap.py`). It is inside on everything; without it the second set's shear totals are 11, 6, 11 and
8 of 11. Beyond that, 29 of 55 first-set and 11 of 22 second-set cases use an input file that is also
in the development set under another loading. The first set was scored at ten points during the work
(`totals.json`) and its failing kinds were fed back by the owner's leave. The second set was scored
once and tells the same story (P1 100 % on both, P2 57 % and 58 %), which is the best evidence here
that the first-set scores are not an artefact of repeated scoring.
Confidence: high on the counts; medium on how much the shared input files matter.

> **The developer's answer (S2).** Agreed. The duplicate is the developer's miss: when 18 development cases were added in increment 8 they were checked against the first set's recipe and not the second's, and the test that guards the two sets apart compared file names. The set is frozen and the case is counted as scored; the sign-off page names it and gives the totals without it. On independence: every held-out case differs from every development case in its input or its loading, but half share a section file with one; "not tuned against" holds for the case, not for the section.

**S3. The shear priority 1 score is fair only when read as "up to Response's last stage".**
See R5 and R6. Read as "r2c gives Response's shear strength" it would be 22 of 28 and 11 of 12.

> **The developer's answer (S3).** Agreed; the sign-off page reads it that way and gives both numbers.

**S4. Three smaller leniencies, none of which moves a live target.**
(1) Two checks outside target are left unassessed as spikes of Response: h-deep-m2v principal tensile
stress 6.8 % and h-nb-m3v shear on crack 7.0 %; counting the second would make first-set shear
priority 2 15 of 28. (2) The view measure forgives a spike displaced by a layer (M2), for r2c and for
Response against itself alike. (3) The ending measure counts four endings of a different kind as
inside (M10). Shear priority 3 meets its threshold by one case (25 of 28 against 86.3 %); the second
set has 12 of 12.
Confidence: high.

> **The developer's answer (S4).** Agreed. None of the three was chosen at the finish: the spike rule and the ending measure are as the owner fixed them.

## What r2c can be trusted for

- **Moment and axial load, no shear: yes, as a stand-in for Response.** On all 37 held-out cases the
  strength, the whole moment-curvature curve including its ending, and every detail view agree with
  Response; strengths to 0.01 %. r2c agrees with Response here better than Response agrees with itself
  after a 0.05 % change of concrete strength (27 of 27 against 20 of 27 on priority 1).
- **With shear, the response up to the point where Response stops: yes.** On all 40 held-out shear
  cases the peak is within 0.5 % and the rising curve within 1.5 % over the range Response covers.
- **With shear, the shear strength r2c reports: not as Response's number without a check.** On 6 of 40
  held-out shear cases r2c's response goes on past Response's last stage to a load 5 to 32 % higher,
  and r2c's output does not mark where Response stopped. Response's lower figure is repeatable in most
  of them. Whether the higher figure is the better answer the evidence cannot say; it is not
  Response's answer. Until r2c marks that stage, compare its peak with Response's on any section
  where r2c's response has a sudden jump in load or a long tail of closely spaced stages.
- **With shear, the detail views at the peak: the strains and stresses broadly, not every view at
  every layer.** About four cases in ten have at least one view more than 5 % out at the peak
  (priority 2: 16 of 28 and 7 of 12 inside; Response against itself 18 of 28 and 5 of 12). The
  differences are local: the transverse bond view (low by 8 to 28 % of the chart's largest value),
  shear stress and shear on crack in the few layers at a change of web width, the position of the
  crack front by a layer or two, and the steel stress at a crack when material factors are used. Do
  not read a single layer's value at a flange-web junction off either program.
- **With shear, after the peak: no.** r2c ends at the peak where Response records a collapse, or runs
  on far past where Response stops. The owner already treats this as reported only.
- **Not shown by this evidence:** anything outside the 77 cases (other shapes, other loadings),
  whether r2c's states beyond Response's last stage are properly converged, run time, and interface
  parity.

> **The developer's answer (what r2c can be trusted for).** Agreed, line for line. It is
> the basis of the sign-off page (`docs/summary.md`) and of the README's known limitations.
