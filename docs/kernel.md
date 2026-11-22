# The kernel

What r2c computes, and where each rule comes from. Three sources, marked in the text:

* **[T]** Bentz, *Sectional Analysis of Reinforced Concrete Members* (PhD thesis, University of
  Toronto, 2000), chapters 3 to 7 and its Appendix A (the Response-2000 manual). The structure
  of the kernel is the thesis': MCFT at a node, the crack check, dynamic layering, the
  longitudinal stiffness method, the nested solution loops.
* **[B]** The Response-2000 1.9.7 program itself, read with a decompiler to answer a specific
  question the thesis leaves open (a constant, a default, the exact form of a rule). Where a
  routine's address is given, `tools/decompile.py` shows it.
* **[O]** Inferred from Response's output (the oracle, through r2x): fitted or deduced, not
  read anywhere. These are the weakest and are listed again at the end.

How much came from where, plainly: the thesis gives the method, but Response 1.9.7 differs
from it in many details, and matching the program stage for stage needed the program's own
rules. The node routine, the flexural crack check, the crack spacing and bond tables, the
cracking strength table and the derived steel properties below follow the binary; the thesis
was the map for finding and understanding them. None of Response's code or data is in r2c.

Units inside r2c: mm, MPa, N, plain strain. Tension positive; moment positive with compression
on top.

## Geometry and strain state

Depth z is measured up from the bottom; charts use y = z − zc, zc the centroid of the gross
concrete, or y = z − za where a moment axis za is given: Response's detail views measure
depth from the moment axis and its axial strain on the control charts is the strain there
[O: newbeam-axialloc-nm, whose Longitudinal Strain chart runs from +400 to −200 mm with the
axis 200 mm above the bottom]. Moments are taken about that axis. Plane sections: εx(y) = εx0 − φ·y. The shear strain is γ(y) = γ0·s(y), s a profile of
mean one over the width-weighted depth [T 7-3]. Concrete is taken net of the bars (a bar's
force is As·(fs − fc)) [O].

The outline is the list of (height, width) rows of the input, straight between rows; two rows
at one height make a step in width (a flange). Quick Define writes a circle as 13 such rows,
points of the circle every 15°, and Response analyses those rows as they are, straight between
them [O: the column's peak under axial load alone agrees within 0.01 % with the polygon's
area; the circle has 1.1 % more]. The curved segments of the manual (a row whose width is UP
or DOWN [T, Appendix A 2-4 and 5-9]) cannot be in an input file: Response's XML reader
rejects them, and r2c does as an input error [O: measured with r2x, `docs/scope.md` 1.4;
B: the two words are used by the reader of shape.dat `004f96e0` and the outline dialog's
width field `00448d90` only]. A shape given without an outline (which Response opens with no
concrete and cannot solve) is given the rows Response writes when the shape is defined in
it; for a circle, the 13 rows [O; not compared].

Shrinkage and thermal strain of the concrete, εsh(z), is the strain the concrete would take
up unrestrained: a node's concrete strain is εx(z) − εsh(z), and the bars' is not changed.
The profile is a parabola through the points given [T, manual 3-5: "parabolically
interpolates between these points"; O: Response's Shrinkage & Thermal Strain chart for three
points is the parabola through them (newbeam-thermgrad-m)]: straight between two points,
constant beyond the end points; with more than three points, the parabola through the three
nearest [O, r2c's own reading of "parabolically"; not compared]. A bar layer's thermal strain
is taken off its prestrain [T, manual 3-5: "can be used the same way as prestrains"].

## Concrete

* Automatic properties: Ec = 3320√fc′ + 6900; n = 0.8 + fc′/17; ε0 = (fc′/Ec)·n/(n − 1) [T].
  Automatic tensile strength ft = min(0.15·fc′, 1.4·(1 + 0.01·fc′)) MPa, not the thesis'
  0.45·fc′^0.4 [B]. The stiffness used for cracking strains is the secant at −0.1 mm/m [B].
* Base curves: linear, parabola, Popovics/Thorenfeldt/Collins (default), elastic-plastic,
  segmental [T, manual Table 2-1]. For a segmental curve the peak is the largest stress of the
  segments.
* Compression softening: see "Compression softening" below.
* Tension stiffening, by number [T, manual Table 2-1; B `004ad9c0`]: 0 none; 1
  Vecchio-Collins 1982, ft/(1 + √(200·ε1)); 2 Collins-Mitchell 1987, ft/(1 + √(500·ε1)); 3
  Izumo et al, ft to 2·εcr and ft·(2εcr/ε1)^0.4 beyond; 4 Tamai et al, ft·(εcr/ε1)^0.4; 6
  elasto-plastic, ft; 7 (default) Bentz 1999, f1 = ft/(1 + √(M·ε1)), M the bond parameter
  from the bars near the node [T 4]. All times the tension stiffening factor. 5 is refused,
  as Response refuses it. In Response's own peak states r2c's forces agree within 0.4 % for
  1, 2, 3, 4 and 6 (measured 2026-11-21, `tools/diagnose.py states`). "None" cannot be
  compared: Response asks a question before solving that r2x does not answer.
* After cracking the tension has a floor Ec·εcr/(1 + 250·w) (w in mm) [B].
* Aggregate size for shear on the crack falls linearly to zero between 60 and 70 MPa, and is
  capped at 25 mm [T, B]. vci,max = 0.18√fc′/(0.31 + 24w/(a + 16)) [T].
* The material factor multiplies every concrete stress.

### Compression softening [B `004ad9c0`, set-up `004ac190`]

β lowers the compressive strength with the principal tensile strain ε1 (taken as zero when
negative); ε2 is the compressive strain itself, ε0 the strain at peak stress, fc′ in MPa,
strains as plain numbers, magnitudes throughout. The numbers are the file's `c_soft`, the
names those of Response's dialog [T, manual Table 2-1 for the names; the rules, constants
and exponents are the binary's].

| No. | Model | β (never above 1 unless said) | Strain at peak stress |
|---:|---|---|---|
| 0 | None | 1 | ε0 |
| 1 | Vecchio-Collins 1982 | 1/(0.85 + 0.27·ε1/ε2) | β·ε0 |
| 2 | Vecchio-Collins 1986 | 1/(0.8 + 0.34·ε1/ε0) | ε0 |
| 3 | Vecchio-Collins 1992-A | 1/(1 + Kf·Kc), Kc = 0.35·(ε1/ε2 − 0.28)^0.8, zero below 0.28 | see below |
| 4 | no name in the dialogs | 1/(1 + Kf·0.23·ε1/ε2) | see below |
| 5 | Vecchio-Collins 1992-B | 1/(1 + 0.27·(ε1/ε0 − 0.37)) (Kf is 1 for this model) | ε0 |
| 6 | Mehlhorn et al | 1/(0.8 + 0.34·ε1/ε0), not below 0.8 | ε0 |
| 7 | Maekawa et al | 1.15 − 125·ε1, between 0.65 and 1 | ε0 |
| 8 | Noguchi et al | below 60 MPa 1/(0.27 + 0.96·(ε1/ε0)^0.167); from 60 MPa 1/(0.8 + 0.6·(ε1 + 0.0002)^0.39) | ε0 |
| 9 | Belarbi-Hsu proportional | 0.9/√(1 + 400·ε1) | β·ε0 |
| 10 | CAN CSA A23.3 M84 | 1/(0.8 + 170·ε1) | ε0 |
| 11 | Collins 1978 | 3.6/(1 + 2·(ε1 + ε2)/ε0) | β·ε0 |
| 12 | Kaufmann-Marti 1998 | fc′^0.6667/(0.4 + 30·ε1)/fc′ | ε0 |
| 13 | Porasz-Collins 1988 | 1/((0.9 + 0.0045·fc′)·(0.8 + 0.34·ε1/ε0)) | ε0 |
| 14, 16, 17 | Zhang-Hsu 1998, Zhu-Hsu-Lee 2001 | min(0.9, 5.8/√fc′)/√(1 + 400·ε1/η), η = 1 (below) | β·ε0 |
| 15 | Hsu 1993 | 0.9/√(1 + 600·ε1) | β·ε0 |
| 18 | Collins-Bentz 2011 (default) | 1/(0.8 + max(170, 3·fc′)·ε1) | ε0 |

Kf = max(1, 0.1825·√fc′). The peak stress is β·fc′ and the base curve is followed in
ε2 over the strain at peak stress, with these particulars:

* Popovics: n = max(1.1, 0.8 + f/17) and, past the peak strain, k = max(1, 0.67 + f/62), f
  the lowered peak stress; for models 3 and 4, n is that of the unlowered strength.
* Models 3 and 4: up to β·ε0 the curve with peak β·fc′ at β·ε0; from there to ε0 a plateau
  at β·fc′; past ε0 the unlowered curve times β.
* Parabola with models 1, 9, 14 to 17: past the lowered peak strain εp the stress is
  β·fc′·(1 − ((ε2 − εp)/(2·ε0 − εp))²), running out at 2·ε0 (4·ε0 for model 16).
* Segmental: the curve's stress times β.

η of the Hsu models is the ratio of the steel's strengths in the two directions; Response
sets it, and the Houston models' own tensile strength 0.31·√fc′, only when one of 9, 14 to
17 is combined with Tamai tension stiffening (its "RA-STM mode") [B `004fbf70`, `004aefa0`];
otherwise η = 1. That combination is not built in r2c and not compared (`docs/scope.md`).
Response's messages that some models are "only defined for the parabolic base curve" are
not raised when a file is opened and solved, and the concrete's set-up does not change the
base curve [B `004ac190`; O: no message in the probes].

How well r2c follows these [measured 2026-11-21 with `tools/diagnose.py states` on the
captures of every stage, r2c put in Response's own peak state with its history]: moment
within 0.4 %, shear within 1 % for the models whose peak comes after softening has set in (2,
6, 7, 9 to 15); for 0, 1, 3, 4, 5 and 8 Response's response ends soon after the web cracks,
before softening acts, and its peak state agrees within 3 % in shear. The numbers of 2, 6, 7,
10 and 13 were in r2c before with formulas that had no source; 2, 6, 7, 10 and 13 turned out
as the binary has them.

## Reinforcement

* Bars: linear, a plateau to εsh, a parabola with its vertex at (εu, fu) [T]. The curve
  carries on down past εu; the bar ruptures at εsh + 1.5·(εu − εsh) [B]. With material factors
  in effect the stress is capped at fy [O].
* Tendons: Ramberg-Osgood [T]. Response derives the rest: the strength is capped at the
  curve's value at the rupture strain, and "yield" is 0.9 of the strength [B].
* Bars with a segmental curve (points of strain and stress in the `<rebar>` element): the
  stress is read off the curve, straight between points, the same in compression; past the
  last point the bar has ruptured. Response derives the properties the rest of the analysis
  uses [B `004ab4e0`, `004aea40`]: the stiffness from the stress at 0.5 mm/m; the strength
  and its strain from the highest point; yield where the curve meets the line of that
  stiffness offset by 2 mm/m (the strength, if it never does); in place of the strain at
  strain hardening, the strain at which the curve passes 1.001 times yield; rupture at the
  last point that carries more than 1 % of yield. For the curve of newbeam-segsteel-m
  Response's own Save As writes fy 412.9 MPa and εsh 4.1 mm/m, and r2c derives the same
  [O]. A segmental curve given for prestressing steel is dropped by Response on reading and
  changes nothing [O: probe igirder-segstrand].
* Interlocking hoops (stirrup pattern 6) are analysed as stirrups, not by the hoop rule
  below [O: on the circular column Response's result with pattern 6 is not its result with
  a hoop; r2c as stirrups is within 0.8 % in shear in Response's peak state]. Patterns 1, 2,
  3 and 5 give the same charts byte for byte in Response on a rectangular section; a
  horizontal tie (7) differs in the Transverse Average Bond chart only [O: the probes].
* Draped tendons: the drape is read and **not used**. Its rule was not found (the thesis
  shows results, 10-10, and no rule; the layer's drape field could not be followed into the
  analysis in a few steps of the binary). Measured: a drape of 0.05 on eight of twelve
  strands changes Response's peak by under 0.1 %.
* Unloading is elastic from a plastic strain kept per layer; it is tracked from the first load
  stage after the initial one [O]. Stirrups keep a plastic strain by depth [O].

## The node [T 3, 4; details B]

For (εx, γ) at a node the transverse strain εy is found so that the concrete's transverse
stress and the stirrups balance. The node routine gives the average stresses from the MCFT and
applies the crack check: the tension f1 is limited by what the steel crossing the crack can
still take (longitudinal reserve f1cx, transverse reserve f1cy) and by shear on the crack,
with Bentz's lower bound 0.25·ft/(0.31 + 24w/(a + 16)). Crack width w = (ε1 − εcr)·sθ,
sθ = 1/(|sin θ|/smx + |cos θ|/smy).

Tables over the depth (100 stations) [B]:

* longitudinal crack spacing: least over the layers of 2·c + 0.1·db/ρ, c the diagonal distance
  to the nearest bar, ρ the steel within 7.5 db over the concrete in that band; never more than
  the depth;
* transverse crack spacing: 2·c + 0.1·db/ρv inside the stirrups' depth, five times the section
  depth outside;
* the bond parameter M: from the bars' perimeters within 7.5 db, falling to nothing one crack
  spacing away; M = 3.6·b·s/(π·db·legs) for stirrups; the lesser governs;
* the steel ratio for the strain concentration of stirrups at a crack.

### Cracking under compression [B `0046a960`; drawn only]

Response's crack-strain routine, called by the node [`0046aaa0`, `004a7b60`], scales the
cracking strain and the cracking stress of a node by

    k = 1.05 − f2/f2max, held between 0.05 and 1,

f2 the principal compressive stress and f2max its softened strength at that node; k = 0.05
once the principal compressive strain (net of shrinkage) is past the strain at peak stress.
Then (a) the node counts as cracked when ε1 exceeds k·εcr, and the crack width and the floor
after cracking are measured from k·εcr; (b) f1 is held to k times the cracking stress; (c)
the line on the Principal Tensile Stress chart is k times the cracking stress where the node
is uncracked. The rule is on in every analysis r2c covers (a flag, `00569f58`, clears it for
one code-based analysis type only) and skipped for a concrete type named "steel".

**r2c applies (c) only**: the drawn line (`NodeOut.f1draw`; for a cracked node, the node's
own limit held under the lowered stress and above the floor). (a) and (b) are not applied:
the node's cracking strain and f1 are as before. Measured 2026-11-21: with (a) and (b) in
the node, nothing moves without shear (ε1 is not tensile where there is compression), but
with shear 15 checks that are inside target go outside while 48 come inside
(`docs/verification.md`, "Principal tensile stress"); taking it over is option F1 in
`docs/status.md`. Whether the thesis describes this rule was not checked: the thesis was not
at hand in the session that read it.

## Flexural cracking strength [B]

With an automatic ft, each face gets a cracking strength fr = min(0.15·fc′,
2.5·(1 + 1.75·fc′/D)), D twice the depth of the tension zone at cracking under the loads being
applied (found by iteration on the transformed section), falling linearly from the face to
nothing at D/2 and never below ft.

## Flexural crack check [T 4-5; details B]

Per tension zone, the moment the bars can still add about the neutral axis at a crack,
Σ As·(cap − fs)·lever, limits the average concrete tension over the zone, by a profile of up to
three parts (uniform; 0.6·ft at the face; 3·ft at the neutral axis).

The capacity at a crack is the bare-bar stress at a concentrated strain
k·ε + prestrain + (εsh − fy/E), k = max(1, 0.014/ρ) (0.625 of that for strands), never less
than yield; ρ is all the steel on the layer's side of the centroid over 0.8·Ag [B]. Steel
that has yielded on average and whose concentrated strain passes the end of its curve
ruptures at the crack and is removed.

### At a step in width [O]

Where the width steps (web to flange) the shear stress and the shear strain jump with it, and
the node above and the node below the step are different nodes at one height. Response's own
charts show the same: three points 0.05 mm apart at each step, the shear strain a quarter
across a step to four times the width (measured, I-girder, M/V = 2 m). In r2c:

* the shear strain profile has a point on each side of every step, and a layer's node on a
  step reads the profile on the layer's own side;
* a node's stirrup ratio ρv = Av/(b·s) is taken with the width of the node's own layer.

Both are r2c's own way of keeping the two sides apart, not rules read from Response. The
tables over the depth (crack spacing, bond, steel ratio at a crack) are still interpolated
across a step from their 100 stations.

### Hoops [T 7-6]

A hoop's strain is the transverse strain times sin²α and only the transverse component of
its force counts (times sin α), α the angle between the hoop and the direction of no strain
[T 7-6, eq. 7-7]. Response's Stirrup Stress chart follows this: 86.2 MPa at a transverse
strain of 0.660 mm/m where sin²α = 0.652, and 110.1 MPa at 0.569 mm/m where it is 0.967
(measured, column with M/V = 1 m, stage 30; the hoop's radius is half the depth between
`disttop` and `distbot`). The plastic strain a stirrup unloads from (Reinforcement, above)
is kept in the hoop's own strain.

## Layers [T 7-3]

Layers of three nodes, integrated by Simpson's rule: a base grid of h/14 with breaks at bar
levels and outline corners; a layer is split when a quarter-point stress is more than 0.2 %
(of the largest stress) off the parabola through its nodes, or the crack state differs across
it; no thinner than h/512. The base grid and thresholds are r2c's [O]: Response's node depths
are close to these but not the same.

## Shear [T 6, 7]

The longitudinal stiffness method: the nodes' tangent stiffness, condensed for no change of
transverse stress, gives the change of longitudinal stress along the member for a unit of
shear; integrated from the top it gives the shear flow, hence a shear stress profile. That is
turned into a new strain profile by the nodes' secant stiffness (tangent where there is no
shear yet) and the state is solved again, until the calculated stresses and those of the state
differ by less than 1 % of the shear force. The reported shear strain is the average weighted
by the shear stress [O]. Bond charts are the change of bar (or stirrup) force along the member
over the bar surface; r2c's transverse bond is a numerical derivative and is approximate.

### The stiffness in the shear flow calculation [B]

Read from the binary on 2026-11-19 (routines `0041e840`, `0041fe20`, `00427cd0`, `0046b940`,
`004201e0`, `004a8710`, `004ae630`, `00440ea0`; how it was read is in session log
2026-11-19-04). Until then r2c differentiated its whole node routine numerically, crack check
included, which is not what Response does and was the cause of responses ending short.

* **The node** [`0046b940`]. Analytic, in the principal directions. Along the principal
  compression: the slope of the compression curve, with the softening by the principal
  tension counted for the changes of longitudinal and transverse strain but not for the
  change of shear strain. Between the two: the secant shear stiffness
  (f1 − f2)/(2(ε1 − ε2)). Along the principal tension it depends on what set the tension f1
  in the node routine (`0046aaa0` records it):
  * the average relation (uncracked, tension stiffening, or Bentz's lower bound): the slope
    of the tension stiffening curve, Ec·φ up to the cracking strain;
  * the reserve of the steel at a crack (x and y together, or one of them with the shear on
    the crack below its limit), or the floor after cracking: nothing;
  * one steel's reserve with the shear on the crack at its limit (f1 = cx + vci,max/tan θ or
    cy + vci,max·tan θ): the derivative of that expression with the reserve held constant;
    the limit's own slope against the crack width is taken with 0.3 where the limit has 0.31.
  The matrix this gives is not symmetric; r2c forms it term by term as Response does.
* **Stirrups** [`004a8710`, `004ae630`]: the slope of the steel's loading curve at the total
  strain. Nothing on the yield plateau; no elastic stiffness for a stirrup that is unloading
  from a plastic strain (reading: the routine's test for unloading compares two stresses
  that are equal when the steel unloads; variants with elastic unloading fit Response's
  states worse, measured, session log).
* **Condensation** [`00427cd0`]: for no change of transverse stress, as before (thesis 6-4).
* **Longitudinal bars** [`004201e0`]: the larger of the slope of the loading curve at the
  average strain and at the concentrated strain at a crack (k·ε + prestrain + εsh − fy/E,
  the strain of the capacity at a crack), less the concrete displaced. On the hardening
  branch the slope's magnitude is used, past the strain at peak stress too. Nothing for a
  bar that has ruptured. This replaces the rule inferred from output on 2026-11-19 (the
  slope at the start of strain hardening for a bar on its plateau), which was this rule's
  value at one strain.
* **The depth that counts** [`00440ea0`, `00427cd0`]: concrete and bars outside a range
  (zlo, zhi) have no stiffness. At a face cracked in flexure the range ends at the outer
  edge of the outermost bar in the cracked zone that still has stiffness, or at the crack
  front if there is none; at a face compressed past the strain at peak stress, where that
  strain is reached. A node whose principal compressive strain is past the strain at peak
  stress has none either.
* **Not taken over**: a "long. nonlinear distribution" of strain added to the plane-section
  change (a table that nothing in the cases compared fills; it belongs to features out of
  scope), and Response's handling of a state with no stiffness at all (r2c reports no state).

The iteration, its damping and what happens when it does not converge are still r2c's own:
fixed damping, at most 30 passes; the closest iterate is accepted if it is within 3 %
[r2c's own; 5 % until 2026-11-19]; otherwise the response ends. Response's own profile
update was read in passing [`0041e840`: each point's shear strain is scaled by the mean of 1
and the ratio of calculated to state stress, within bounds] and is close to r2c's; its
acceptance and step control (`00418af0`, `00424c60`) were not taken over. The driver's
search beyond a state it could not find (r2c's own, from the first build) was removed on
2026-11-19: with the stiffness right it carried the Newbeam at M/V = 1 m 22 % past
Response's failure.

Measured with `tools/diagnose.py flow` (2026-11-19, r2c in Response's own states): r2c's
calculated shear stress is as close to the state's as Response's own two lines are (within 1
point of Response's figure) at every stage of Marshall, se100 and the Newbeam at M/V = 1 m
with and without axial load, and at all but one stage of shear alone; at M/V = 2 m to stage 78 of 87 (2 % at the end, was 13
to 35 % from stage 57); at M/V = 0.5 m to stage 39 (was 7 to 27 % from 37). What is left: 3
to 7 % after the load has fallen and is recovering (M/V = 0.5 m from stage 41; US case from
31), and 2 to 5 % on Liping LB1 from stage 13. Not explained.

## The state under the constant loads [T 7-3; O]

The first load stage is the state under the constant loads alone. It is found by Newton
iteration on the strain at the centroid and the curvature, each step cut back until it
lowers the residual (a section cracked by its own shrinkage or prestrains has a kink there).
It starts from the unstrained section, and if no state is found from there, from the plane
that fits the section's own strains: the shrinkage profile, then the strains at which the
prestrained bars carry nothing [T 7-3: with shrinkage the first estimate is "a linear fit to
those profiles"; the second plane and the cut-back are r2c's own].

## Load stages [O, all of it]

Response's stepping is not described in the thesis and was deduced from its output:

* Control variable: the strain at the centroid if the axial load is being increased; else
  the curvature if the moment is; else the shear strain.
* With moment and shear, once shear governs Response's stages step in the shear strain (about
  10 % a stage on its Shear - γxy chart) while the curvature stalls or turns back, through
  zero in one case (Newbeam M/V = 0.5 m from stage 36; US units, M/V = 1 ft, from stage 27).
  What makes Response change over is not known. r2c's own rule: when no state is found at a
  larger curvature, nor part of the way, and the stirrups are past half of yield or have
  yielded before, it carries on in the reported shear strain with the same step rule.
* The control variable's value at the initial stage is the curvature or the centroid's
  strain there; stepping in the shear strain starts from zero.
* First step Δ0: 0.2 mm/m ÷ h in curvature (0.08 with shear; halved with a constant axial
  load); ε0/20 in axial strain; 0.024 mm/m in shear strain. Stages at Δ0/6 and 7Δ0/6, then
  each step is the larger of Δ0 and 10 % of the control value.
* When a step contains first cracking or the extreme fibre reaching ε0, the event is
  approached in steps of a fifth of what remains, on two levels. Bar rupture: a fifth of the
  step, or a twenty-fifth, if that stops short of the rupture.
* The response ends when the extreme compressive strain passes 4·ε0, when no state can be
  found at a target nor at a half, quarter and eighth of the step, when the load has run out,
  after 101 stages, and (r2c's own rules, where Response's are not known) when less than half
  of the peak is left after a shear failure or less than a fifth after a rupture.
* More Detail adds a stage between every two up to the peak, to at most 327 stages.

## Inferred or fitted values, in one place

| What | Value | Basis |
|---|---|---|
| Stepping rules and end rules | above | Response's control charts |
| Layering thresholds | above | chosen; results insensitive at the tolerances reported |
| Start of unloading tracking | stage 1 | one prestressed case (Cm4) |
| Stirrup plastic strain kept by depth | yes | one case (Newbeam, M/V = 2 m) |
| The two sides of a step in width kept apart | profile and stirrup ratio | r2c's own; Response's charts show both sides (I-girder) |
| A circle from Quick Define is its 13 rows, straight between | yes | one case (column, N alone) |
| Shear profile tolerance | 1 % of V | Response's accepted stages measure 0 to 1 % |
| Closest iterate accepted | within 3 % of V | r2c's own, chosen 2026-11-19 from two cases before the stiffness rules were read; not revisited since |
| Change to shear strain control | no state at a larger curvature; stirrups past 0.5 fy | r2c's own trigger; that Response steps in the shear strain is from two cases |
| Shear-only control on the weighted strain | 0.024 mm/m | one case |
| Factored steel capped at fy | yes | one case (CSA factors) |
| Shrinkage profile through more than three points | parabola through the nearest three | r2c's own reading of the manual; three points compared |
| Interlocking hoops are stirrups | yes | one case (column, M/V = 1 m) |
| A shape without an outline | the rows Response writes for it | not compared: Response cannot solve such a file |
| Second starting plane and step cut-back for the initial state | above | r2c's own; three cases |

## Not implemented

Out of scope by the owner's decision: hollow sections, long-term effects, strain
discontinuity, the old text input format. r2c refuses these and nothing else as out of
scope; what Response itself rejects is an input error (`docs/scope.md`, section 3).

Read and not used: a tendon's drape (Reinforcement, above). Not built: the Hsu softening
models with Tamai tension stiffening (η and the tensile strength of "RA-STM mode"; Compression
softening, above). Not applied in the node: the lowering of the cracking strain and of f1 by
compression (above, "Cracking under compression": the chart's line is lowered, the node's
cracking is not).
