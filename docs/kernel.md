# The kernel

What r2c computes, and where each rule comes from. Three sources, marked in the text:

* **[T]** Bentz, *Sectional Analysis of Reinforced Concrete Members* (PhD thesis, University of
  Toronto, 2000), chapters 3 to 7 and its Appendix A (the Response-2000 manual). The structure
  of the kernel is the thesis': MCFT at a node, the crack check, dynamic layering, the
  longitudinal stiffness method, the nested solution loops.
* **[B]** The Response-2000 1.9.7 program itself, read with a decompiler to answer a specific
  question the thesis leaves open (a constant, a default, the exact form of a rule).
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
force is As·(fs − fc)) [O]. Curved outline segments are read as straight (not implemented).

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

In that calculation a bar on its yield plateau (yielded on average, not yet hardening, not
unloading) is given the slope of its curve at the start of strain hardening,
2·(fu − fy)/(εu − εsh), in place of the zero of the plateau [O]. Fitted at Response's own
states on three steels (`tools/diagnose.py flow --fit-layer`, measured 2026-11-19): Newbeam
4050 to 4200 MPa against 4301; se100 3440 to 3670 against 3675; Marshall 4850 to 5040 against
4914 (the same fit gives 190 000 to 197 000 for an elastic bar of 200 000). A fixed share of
E would not fit all three. Only bars in tension were observed; r2c applies it in compression
too. Not applied to tendons, nor with material factors in effect (not observed).

The iteration is r2c's own, with fixed damping. When it does not converge r2c takes the
closest iterate if it is within 3 % [r2c's own; 5 % until 2026-11-19], looks for a state
further along, and otherwise ends the response.

Known weakness, restated 2026-11-19: where r2c ends short of Response the cause found so far
is not the iteration but the stiffness the calculation uses. `tools/diagnose.py flow` puts
r2c in Response's own states: Response's two shear stress lines agree within 1 % there, and
where r2c's do not, no iteration can settle on that state. The plateau rule above removed one
such difference. One remains, once the stirrups have yielded over much of the depth (Newbeam
M/V = 2 m from stage 57, 13 to 35 %; M/V = 0.5 m at stages 37 to 43, 7 to 27 %): there the
change of shear strain along the member that r2c solves for differs from what Response's
profile implies. Not resolved (docs/verification.md).

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
| Shear profile tolerance | 1 % of V | Response's accepted stages measure 0 to 1 % |
| Closest iterate accepted | within 3 % of V | r2c's own; stages it finds on Newbeam M/V = 2 m measure up to 2.6 %, the iterates that carried M/V = 1 m past Response's failure 4 to 5 % |
| Bar on its yield plateau, in the shear flow | slope at the start of hardening | fitted at Response's states, three steels |
| Change to shear strain control | no state at a larger curvature; stirrups past 0.5 fy | r2c's own trigger; that Response steps in the shear strain is from two cases |
| Shear-only control on the weighted strain | 0.024 mm/m | one case |
| Factored steel capped at fy | yes | one case (CSA factors) |

## Not implemented

Hollow sections, long-term effects, strain discontinuity, the old text input format, curved
outline segments, and the reduction Response draws for the cracking stress in the compression
zone on the Principal Tensile Stress chart (the stress line itself is not affected in the
cases compared).
