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
concrete. Plane sections: εx(y) = εx0 − φ·y. The shear strain is γ(y) = γ0·s(y), s a profile of
mean one over the width-weighted depth [T 7-3]. Concrete is taken net of the bars (a bar's
force is As·(fs − fc)) [O].

The outline is the list of (height, width) rows of the input, straight between rows; two rows
at one height make a step in width (a flange). Quick Define writes a circle as 13 such rows,
points of the circle every 15°, and Response analyses those rows as they are, straight between
them [O: the column's peak under axial load alone agrees within 0.01 % with the polygon's
area; the circle has 1.1 % more]. The curved segments of the thesis (a row whose width is UP
or DOWN, an elliptical transition between its neighbours [T, Appendix A 2-4 and 5-9]) are not
implemented: no input compared so far has one.

## Concrete

* Automatic properties: Ec = 3320√fc′ + 6900; n = 0.8 + fc′/17; ε0 = (fc′/Ec)·n/(n − 1) [T].
  Automatic tensile strength ft = min(0.15·fc′, 1.4·(1 + 0.01·fc′)) MPa, not the thesis'
  0.45·fc′^0.4 [B]. The stiffness used for cracking strains is the secant at −0.1 mm/m [B].
* Base curves: linear, parabola, Popovics/Thorenfeldt/Collins (default), elastic-plastic,
  segmental [T, manual Table 2-1]. For a segmental curve the peak is the largest stress of the
  segments.
* Compression softening by the principal tensile strain: none, Vecchio-Collins 1982 and 1986,
  Porasz, and the default 1/(0.8 + max(170, 3·fc′)·ε1) [T; the default's form B].
* Tension stiffening: the manual's models; the default is Bentz 1999,
  f1 = ft/(1 + √(M·ε1)), M the bond parameter from the bars near the node [T 4].
* After cracking the tension has a floor Ec·εcr/(1 + 250·w) (w in mm) [B].
* Aggregate size for shear on the crack falls linearly to zero between 60 and 70 MPa, and is
  capped at 25 mm [T, B]. vci,max = 0.18√fc′/(0.31 + 24w/(a + 16)) [T].
* The material factor multiplies every concrete stress.

## Reinforcement

* Bars: linear, a plateau to εsh, a parabola with its vertex at (εu, fu) [T]. The curve
  carries on down past εu; the bar ruptures at εsh + 1.5·(εu − εsh) [B]. With material factors
  in effect the stress is capped at fy [O].
* Tendons: Ramberg-Osgood [T]. Response derives the rest: the strength is capped at the
  curve's value at the rupture strain, and "yield" is 0.9 of the strength [B].
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

## Not implemented

Hollow sections, long-term effects, strain discontinuity, the old text input format, curved
outline segments (rows with a width of UP or DOWN), and the lowering of the cracking strain and of f1 by compression in the
node (above, "Cracking under compression": the chart's line is lowered, the node's cracking
is not).
