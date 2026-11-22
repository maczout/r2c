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
width field `00448d90` only]. A shape given without an outline, which Response opens with no
concrete and cannot solve, is an input error too [O; owner, 2026-11-22, D6].

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
and exponents are the binary's]. r2c has the models the manual names, and the default. The
thesis itself gives two rules, both in ε1 alone: 1/(0.8 + 170·ε1) for normal strength
concrete, which is number 10 and, up to 56.7 MPa, the default 18; and that times
1/(0.9 + 0.0045·fc′) for high strength concrete [T 5-1, p. 58 to 59]. Not in the manual and
refused as out of scope: 4 (no name in the dialogs), 16 (Zhu-Hsu-Lee 2001) and 17 (Zhang-Hsu
1998, no eta) [owner, 2026-11-22, D10 and D18]. The named models without a rule in the
documents stay, and so does the default [owner, 2026-11-22, D21 and D22].

| No. | Model | β (never above 1 unless said) | Strain at peak stress |
|---:|---|---|---|
| 0 | None | 1 | ε0 |
| 1 | Vecchio-Collins 1982 | 1/(0.85 + 0.27·ε1/ε2) | β·ε0 |
| 2 | Vecchio-Collins 1986 | 1/(0.8 + 0.34·ε1/ε0) | ε0 |
| 3 | Vecchio-Collins 1992-A | 1/(1 + Kf·Kc), Kc = 0.35·(ε1/ε2 − 0.28)^0.8, zero below 0.28 | see below |
| 5 | Vecchio-Collins 1992-B | 1/(1 + 0.27·(ε1/ε0 − 0.37)) (Kf is 1 for this model) | ε0 |
| 6 | Mehlhorn et al | 1/(0.8 + 0.34·ε1/ε0), not below 0.8 | ε0 |
| 7 | Maekawa et al | 1.15 − 125·ε1, between 0.65 and 1 | ε0 |
| 8 | Noguchi et al | below 60 MPa 1/(0.27 + 0.96·(ε1/ε0)^0.167); from 60 MPa 1/(0.8 + 0.6·(ε1 + 0.0002)^0.39) | ε0 |
| 9 | Belarbi-Hsu proportional | 0.9/√(1 + 400·ε1) | β·ε0 |
| 10 | CAN CSA A23.3 M84 | 1/(0.8 + 170·ε1) | ε0 |
| 11 | Collins 1978 | 3.6/(1 + 2·(ε1 + ε2)/ε0) | β·ε0 |
| 12 | Kaufmann-Marti 1998 | fc′^0.6667/(0.4 + 30·ε1)/fc′ | ε0 |
| 13 | Porasz-Collins 1988 | 1/((0.9 + 0.0045·fc′)·(0.8 + 0.34·ε1/ε0)) | ε0 |
| 14 | Hsu-Zhang 1998 | min(0.9, 5.8/√fc′)/√(1 + 400·ε1) | β·ε0 |
| 15 | Hsu 1993 | 0.9/√(1 + 600·ε1) | β·ε0 |
| 18 | Collins-Bentz 2011 (default) | 1/(0.8 + max(170, 3·fc′)·ε1) | ε0 |

Kf = max(1, 0.1825·√fc′). The peak stress is β·fc′ and the base curve is followed in
ε2 over the strain at peak stress, with these particulars:

* Popovics: n = max(1.1, 0.8 + f/17) and, past the peak strain, k = max(1, 0.67 + f/62), f
  the lowered peak stress; for model 3, n is that of the unlowered strength.
* Model 3: up to β·ε0 the curve with peak β·fc′ at β·ε0; from there to ε0 a plateau
  at β·fc′; past ε0 the unlowered curve times β.
* Parabola with models 1, 9, 11, 14 and 15: past the lowered peak strain εp the stress is
  β·fc′·(1 − ((ε2 − εp)/(2·ε0 − εp))²), running out at 2·ε0.
* Segmental: the curve's stress times β.

The Hsu models (9, 14, 15) combined with Tamai tension stiffening are Response's "RA-STM
mode" [T, manual Table 2-1], which runs them with a steel ratio and a tensile strength of
its own. That combination is out of scope and refused [owner, 2026-11-22, D5]; with any
other tension stiffening the models are as in the table.
Response's messages that some models are "only defined for the parabolic base curve" are
not raised when a file is opened and solved, and the concrete's set-up does not change the
base curve [B `004ac190`; O: no message in the probes].

How well r2c follows these [measured 2026-11-21 with `tools/diagnose.py states` on the
captures of every stage, r2c put in Response's own peak state with its history]: moment
within 0.4 %, shear within 1 % for the models whose peak comes after softening has set in (2,
6, 7, 9 to 15); for 0, 1, 3, 5 and 8 Response's response ends soon after the web cracks,
before softening acts, and its peak state agrees within 3 % in shear. The numbers of 2, 6, 7,
10 and 13 were in r2c before with formulas that had no source; 2, 6, 7, 10 and 13 turned out
as the binary has them.

## Reinforcement

* Bars: linear, a plateau to εsh, a parabola with its vertex at (εu, fu) [T]. The curve
  carries on down past εu; the bar ruptures at εsh + 1.5·(εu − εsh) [B]. With material factors
  in effect the stress is capped at fy [O].
* Tendons: Ramberg-Osgood [T]. Response derives the rest: the strength is capped at the
  curve's value at the rupture strain, and "yield" is 0.9 of the strength [B].
* A segmental curve for reinforcing steel (points of strain and stress in the `<rebar>`
  element) is not in the manual, whose curve is the one above [T, manual A-17], and is
  refused as out of scope [owner, 2026-11-22, D18]. One given for prestressing steel is
  dropped by Response on reading and changes nothing [O: probe igirder-segstrand]; r2c does
  not read it.
* Interlocking hoops (stirrup pattern 6) are analysed as stirrups, not by the hoop rule
  below [O: on the circular column Response's result with pattern 6 is not its result with
  a hoop; r2c as stirrups is within 0.8 % in shear in Response's peak state]. Patterns 1, 2,
  3 and 5 give the same charts byte for byte in Response on a rectangular section [O: the
  probes]. A horizontal tie (7) is not in the manual and is refused [owner, 2026-11-22,
  D23], as is a file that holds several sections.
* Draped tendons are out of scope [owner, 2026-11-22, D4]: a layer with a drape other than
  zero is refused.
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

### Cracking under compression [B `0046a960`]

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

**r2c applies all of it since 2026-11-22** (owner, D14; before, only the drawn line (c)).
The thesis does not describe the rule: its node cracks at the cracking strength [T 3-2-2];
this is one of the details where the program is followed. Measured on the phase A set
(`tools/changes.py`, the run before against the run after): nothing moves without shear,
where there is no principal tension across compression. With shear the rising branch at
M/V = 0.5 m comes inside (6.1 to 2.7 %), and 35 view checks with it, 24 of them at two stages
that are now like states (the peak under N₀ then V, the fall at cracking under V alone);
three Should views go outside by a point (shear on crack 4.9 to 5.5 %, average angle 3.7 to
5.1 %) or at one stage (transverse bond under N₀ then M + V at the last stage). The stage
that flipped in the trial of 2026-11-21 does not flip with the stage matching of D13.

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

*When it is removed* [B `004aaf70`, `004ae520`, `0041e310`, `00434c80`]. A bar's stress in
a state is the lesser of its average stress and its capacity at a crack, and nothing at all
when the capacity says it has ruptured: the bar is gone in the state where it ruptures, not
from the stage after. An accepted stage marks its ruptured bars as gone for the stages that
follow; a stage that is set aside marks nothing (the marks are put back from the stage
before). Until 2026-11-22 r2c removed the bar only from the next stage on, so the stage
where it ruptured still carried it [O: −M, the stage after the peak, 84 kNm where Response
has 17].

A tension zone that no bar crosses is limited to zero: its capacity moment is zero and so
is its limit, which leaves the node at its floor after cracking [B `00441d80`, `00440400`;
O: N + M at cracking, 51.5 to 0.3 %]. The thesis has it the other way ("if there are no
bars crossing the crack face, the concrete stress is not reduced", T 4-5, restriction 3);
r2c followed the thesis until 2026-11-22 and follows the program since (D30, D34).

### Steel stress at a crack [T 4-5; B `00442e50`, `00442cd0`, `00440c70`, `004409d0`, `00441d80`]

"The moment caused by the combined principal tension and shear on the crack is computed
about the crack face. An increase in curvature is then calculated about the crack front to
induce the same moment" [T 4-5, last part]. The particulars are the program's, read
2026-11-22 for the two cases where r2c showed no stress at a crack and Response did:

* *About which point.* The neutral axis of the deeper of the two tension zones of the crack
  check (where the strain, net of shrinkage, changes sign), not the crack front. A section
  all in tension has no such axis: Response takes one 1000 m below the section, which makes
  the extra strain the same for every bar, and counts the concrete only when the tension
  grows upwards.
* *The concrete's moment.* Over the halves of layers that are cracked at both ends, on the
  tension side of that axis: (f1 less the floor after cracking, not below zero, plus
  vci/tan θ) times the width times the distance from the axis. The floor here is
  max(ft, the node's cracking strength)/(1 + 250·w).
* *The bars.* Every bar whose strain (without prestrain, net of shrinkage) is tensile takes
  part, cracked concrete around it or not. The extra curvature Δφ₁ that uses up the reserve
  of the first bar to reach its capacity at a crack (reserve/E over its distance from the
  axis; 1 /m at most) is found, and the moment the bars below yield add at it, elastically.
  If that is at least the concrete's moment, the extra curvature is Δφ₁ in the proportion
  of the two moments. If not, and the concrete's moment is within the capacity moment of
  the crack check (0.1 % and 2 N m over), it is solved for with the bars' own curves, each
  held to its capacity at a crack. Otherwise there is no value.
* *What is shown.* A bar in compression shows nothing. A bar in tension shows its stress at
  the extra strain, the lesser of its curve and its capacity at a crack, if the strain at
  its depth with the extra strain reaches the cracking strain there; nothing if it does not.

Before 2026-11-22 r2c took the moment of f1 itself about the crack front, by the bars inside
the cracked depth alone [r2c's reading of the thesis]: a bar above the crack front showed
nothing (N + M at the peak: Response 46 MPa), and under tension the two layers were
treated as two zones (top bar 210 MPa where Response has 37). Measured on the phase A set:
both come to 0.0 %, and the same view comes inside at five stages of four shear cases
(`docs/verification.md`, "A2, part 3").

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

## Layers [T 7-3; B `00434eb0`, `004a9d90`, `004a9be0`]

Layers of three nodes, integrated by Simpson's rule, divided in a binary tree where the
stresses are not interpolated well [T 7-3]. The numbers are the program's, read 2026-11-22
(before, r2c's own, inferred from Response's node depths).

*The base layers* [B `00434eb0`]. Each stretch of the outline between two rows gets
int(8·d/(h + 0.1 mm) + 0.99) − 1 equal layers, at least one (d its depth, h the section's):
seven for a section with one stretch. (The thesis says eight.) Then, bar layer by bar layer,
the layer that holds the bar gets a boundary at the bar's upper edge and one at its lower
edge (the bar's height ± half its diameter, held inside that layer), unless that would
leave a layer thinner than h/2048 or the edge is within 0.2 mm of a boundary. Response also
puts a layer 0.1 mm thick across a step in width; r2c does not, and keeps the two sides of a
step apart in its own way ("At a step in width").

*Splitting* [B `004a9d90`, `004a9be0`]. Each time the section's forces are wanted, the layers
start from the base layers. The middle of each half of a layer is worked out and compared
with the parabola through the layer's three nodes, for f1 and for f2. A half fails when
either is off by more than 0.2 % of the largest value at the nodes of the base layers, or
when the crack front passes through it (ε1 below the cracking strain at one end of the half
and above it at the other; the cracking strain here is not lowered by compression). A layer
with a half that fails is divided in two, provided half its thickness is more than h/1024;
a half that passed becomes a layer that is not looked at again. So the nodes at a crack
front are h/1792 apart on Newbeam (0.33 mm), where r2c's were h/896 apart.

r2c solves a stage on fixed layers, builds the layers again from the base layers for the
state found, and solves again if they changed (up to five times without shear, three with)
[r2c's own arrangement of the same rule]. No more than 220 layers [r2c's own; Response's
limit was not read].

Measured on the phase A set: at the stages looked at (M at the peak and at the end, −M at
the peak, N at the end) r2c's node depths are Response's, node for node
(`docs/verification.md`, "A2, part 2").

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

The iteration, the profile update and what happens when a stage does not converge are
Response's since 2026-11-21 (Load stages, below). Until then they were r2c's own: fixed
damping, up to 30 passes, the closest iterate accepted within 3 %, the response ended
otherwise. The driver's search beyond a state it could not find (r2c's own, from the first
build) was removed on 2026-11-19: with the stiffness right it carried the Newbeam at M/V =
1 m 22 % past Response's failure.

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

## Load stages

**With shear: Response's own load stage control [B]**, taken over 2026-11-21 in place of
r2c's (step 4 of increment S). The rules are in the next section, each as read from the
binary: the control variable and its base step, the stepping and its growth, the closing in
on an event, the passes on a stage and when a stage that has not converged is kept, what
happens when a stage is refused, the change of control variable, the end tests. What r2c
does of its own inside that frame, or reads into it:

* The global strains of a pass are solved by r2c's Newton iteration with its bracketing
  fallback. Response's solve can come back "not closed" and the stage is carried on from;
  r2c's reading of that: the nearest state found, if it is out of balance by less than 2 %
  of the section's scale [O, r2c's own threshold].
* **The shear strain profile is kept at the nodes' own heights** (and on its base grid of
  the tables' heights). On the fixed grid alone it could not follow the closely spaced
  nodes at a crack front, and the profile iteration was left with an error it could not
  remove: 1.6 to 3.8 % in Response's measure, where it now goes under 0.1 % [measured,
  Newbeam at M/V = 1 m, 40 passes on five stages]. That is what lets Response's measure and
  its 1 % and 3 % be used as they are.
* The profile update is Response's [B `0041e840`]: where a node carries shear, its shear
  strain times the mean of one and (calculated stress over the state's stress), that factor
  within ten either way; the profile is then brought back to a mean of one. Where a node
  carries no shear yet, r2c's own: the calculated stress over the node's tangent stiffness.
* Under shear alone, half of the update is taken in the second half of the sixteen passes
  [O, r2c's own, from that one loading: without it the stage past the peak does not settle
  where Response's does; with it under every loading r2c settles where Response's stages
  stand still].
* Shear alone is stepped in the shear strain, 0.02 mm/m a stage, half that under a constant
  compression [O: Response's stages under shear alone are evenly spaced in the shear strain
  while the axial strain stays at nothing; the binary's choice read for the beam gives the
  axial strain there, so shear alone is taken to run in another of its analysis classes,
  whose base steps are those]. No change of control variable under shear alone.
* State code 1's "no reserve" is read as "no stirrup crosses the node"; the shear on the
  crack "at its limit" is what governs the node's tension (The node, above).
* The load compared with "the largest so far" is the load factor. A stage found with the
  loads reversed is not a stage.
* "A large constant axial load" (the base step in curvature is halved) is taken as more
  than 0.1 MPa on the gross area [O: Newbeam under −2000 kN steps at half the base step].

How far this goes [measured, sixth run of 2026-11-21]: on Newbeam at M/V = 1 m r2c's stages
are Response's stage for stage up to the peak (the same curvatures), the control changes to
the shear strain at the same place and the plateau after the peak is Response's (193 kN at
4.5 to 4.8 mm/m). Under shear alone the whole response is Response's, the falling branch
included. Where r2c's profile iteration settles and Response's does not, r2c still goes on
past Response's end, and the last stage often differs (`docs/status.md`, known deviations).

**Without shear [O]**: r2c's own stepping, deduced from Response's control charts before
the binary was read, and now seen to be Response's rule (the next section): the strain at
the centroid if the axial load is being increased, else the curvature; a first step of Δ0/6
(Δ0 = 0.2 mm/m ÷ h in curvature, ε0/20 in axial strain), then Δ0, growing to a tenth of the
control value; an event (first cracking, the extreme fibre reaching ε0) approached in fifths
of what remains. The
response ends when the extreme compressive strain passes 4·ε0, when no state is found at a
target nor at a half, quarter and eighth of the step, and when the load has run out.
Response's end tests for these cases (the next section, 3 to 6) come to the same on the
cases compared.

*Bar rupture within a step, and the end after it* [B `00415e30`, `00419ff0`, `00418fd0`,
`00419990`], since 2026-11-22. A stage in which the number of ruptured bars has changed is
set aside (deleted, unlike the stage set aside at cracking or crushing, which is kept for
later) and a stage is tried a fifth of the way to it, again and again while the step is
more than 1 % of the control variable's travel from the first stage. A stage short of the
rupture is kept and the stepping goes on from it; the last stage tried is kept, ruptured or
not. The response ends at a stage, the eleventh or later, that has less than a fifth of the
peak load and at which nothing new has happened (cracking, crushing, a rupture) since the
stage before. Before, r2c tried a fifth and a twenty-fifth and then kept the whole step,
and ended at the second stage under a fifth of the peak. Measured on −M: the last two
stages are Response's (curvatures 52.25 and 58.02 rad/km, 16.7 and 16.5 kNm); post-peak
20.3 to 0.0 %. Not right yet for a section with several layers of strand: on the parked
I-girder under M the response ended as Response's does before this change and does not
now [O, one run of the parked cases, 2026-11-22; not looked into].

The control variable's value at the initial stage is the curvature or the centroid's strain
there. More Detail adds a stage between every two up to the peak, among the stages found in
the first control variable, to at most 327 stages. A response has at most 101 stages [O].

## The stage solve without shear [B], read 2026-11-22

How Response-2000 finds the state of a stage when there is no shear. Read for increment A3
(`00425f10`, `0041e1e0`, `00425af0`, `004276a0`, `00416730`, `00433c50`, `00418af0`,
`004a9030`). **Written in r2c and not in use**: each of the two solves brings the check it
was read for inside target and moves another Must view outside, so r2c's own solve (the
balanced state, to a root of the unbalanced force) is still the default
(`docs/summary.md`, D35 and D36; `Flexure.own_curvature`, `Flexure.own_axial`).

*Which solve.* Under a stepped curvature, the secant below. Under a stepped axial strain
Response sets its relaxation flag, and with that flag the stage goes to the general solve it
uses with shear.

*The first estimate* of a stage is the strains of the stage before with the stepped one set
to its target (a new stage is a copy of the last; the extrapolation in `00416730` multiplies
by a difference that is zero). When a stage has been set aside beyond the target, the
strains of whichever of the two is nearer in the stepped strain.

*The secant, under a stepped curvature* [`00425f10`]. One unknown, the axial strain. The
unbalanced force is the axial force off the loading line. The state is taken as soon as that
is under 0.1 % of |N| + |M| + |V| plus 1 (N and N m): Response does not go on to the
balanced state. A step is the unbalanced force over the slope, which is the secant's
slope and is carried from one stage's solve to the next; it is found again, by a change
of 0.01 mm/m, for the first stage, for a stage put in between two others and after a
failure. A step is no more than half the concrete's strain at peak stress. After sixteen
tries the steps are halved and the slope is the section's own stiffness; after twenty it
gives up and falls back on halving [`00425af0`]: the axial strain is bracketed in steps of
the strain at peak stress, twelve at most each way, and halved up to thirty times.

*The general solve, under a stepped axial strain* [`004276a0`]. Newton's method on the
section's stiffness, in half steps (the relaxation factor is 0.5 with the flag), and
always at least one. It stops when the squared unbalanced forces over (h + 0.1 mm)² are
under 10⁻⁶·(N² + V² + M²/h²) + 1 + (1000·A)² (N, m; A the gross area, the same quantity
that decides what a large constant axial load is), or after 50 steps, or when a step is
larger than 0.5 in all. The tolerance is wide: on Newbeam under tension the states before
cracking carry 40 to 130 N m of unbalanced moment, each about half a step short of balance
[O: the same figures come out of r2c in Response's states and out of this solve]. That is
how Response has one more rising stage before the fall at cracking than r2c's balanced
solve can find (D31). Still r2c's own in this solve: the stiffness is taken numerically
(Response's is `00427cd0`, which r2c has for the shear cases), and the step for a moment
that grows with the axial load is r2c's reading (`004267c0` was not read).

*A stage put in between that is not solved* [`00418af0`] is dropped, the stage set aside is
taken as it was found, and the event is closed in on no further. A stage set aside and
taken up again is not solved again.

*The sums* [`004a9030`]: Simpson's rule over each layer's three nodes, with the mean of the
top and bottom widths at the middle and a correction where the width tapers; a bar's force
less the concrete it displaces, the concrete's stress there read from the profile. As in
r2c, apart from the correction (no phase A section tapers).

Measured on the eight phase A cases without shear (2026-11-22, `tools/changes.py` against
the run after part 2; `tools/offsets.py` for the strains):

| | The secant on | The general solve on |
|---|---|---|
| Came inside | M, principal tensile stress at the last stage, 7.2 to 0.4 % | tension's shape; its rising branch 0.48 to 0.08 % |
| Went outside | N +200 kN then M, principal tensile stress at the last stage, 1.1 to 6.2 % | at the peak: tension, longitudinal concrete stress and principal tensile stress, 0.2 to 7.6 %; N + M, steel stress at a crack 0.0 to 22.7 % and principal tensile stress 1.7 to 7.7 % |
| r2c's state against Response's | last stage of M: 0.005 to 0.0003 mm/m of axial strain; of N +200 kN then M: 0.024 to 0.005 | N + M: the curvature is off by as much as before (0.003 to 0.025 rad/km), on either side |

## Response's own load stage control [B], read 2026-11-21

Read from the binary for step 4 of increment S (the routines: stage control `00418af0` and
its wrapper `00418860`; a new stage `00415e30`; the next target `0041a870`; the control
variable `00422de0` and its base step `00419250`; the change of control variable `004162d0`;
the end of the response `00419990`; the profile error `00420f20` and the stage's state code
`004204b0`; the single-state solve `00424c60`). This section says what Response does. What
of it r2c has taken over is said under "Load stages" above; until that says otherwise, r2c's
stepping is its own.

**Control variable.** With a = |ΔN|, b = 3·|ΔM|/h and c = |ΔV| (the load increments; h the
section's depth): the curvature if a ≤ b and c ≤ b (the moment dominates, or there is no
increment); else the strain at the moment axis. So shear alone is stepped in the axial
strain, not in the shear strain. The other variable, used after a change (below): where the
moment dominates, the shear strain if there is shear, else the axial strain; where it does
not, the curvature or the shear strain, whichever of b and c is larger, or the axial strain
if shear is the largest and b < a.

**Base step Δ0** of a control variable, fixed when it is chosen:

* curvature: 0.004/h/50 (h in metres, per metre); 0.004/h/20 without shear; halved if
  |ΔV|/2 < |ΔN| with shear, halved again under a large constant axial load, and again if
  M/V < h;
* axial strain: ε0 of the concrete over 20;
* shear strain: 0.02 mm/m where a stirrup spans more than half the depth and the transverse
  steel is above a minimum (0.08·√fc′ MPa of a strength measure), else 0.05 mm/m.

**Stepping.** The first stage after the initial one is at Δ0/6. Each next target is the
previous *target* plus Δ0 times a multiplier, which starts at 1. From the fifth stage, while
the multiplier is not above 1, Δ0 is raised to a tenth of the target's value when it is less
(the 10 % growth seen on the control charts).

**Events.** After a stage is accepted it is compared with the one before: newly cracked
(principal tensile strain above the cracking strain at any node), newly crushing (principal
compressive strain beyond ε0 at any node), a node state of yield or slip at a crack (only
where there are no stirrups), a change in the number of ruptured layers. If there is one,
and the last step is more than 2 % of the travel of the control variable from the start
(0.5 % for crushing, 1 % for rupture), the last stage is set aside and a stage is put at a
fifth of the way to it (four fifths, for a stage that has un-cracked); this repeats on the
shrinking interval, and then the stage set aside is taken up again.

**Accepting a stage.** A stage is worked on in passes: solve the global strains for the
loads at the control value with the shear strain profile as it is; update the profile from
the calculated shear stress; measure the profile error. The error is the standard deviation,
over 50 points of the depth, of the difference between the calculated shear stress and the
shear stress of the state, over the mean calculated shear stress (taken as 0.9 % where the
shear is negligible). After each pass:

* converged below 1 %: the stage is accepted;
* else another pass, up to 16; with the error above 10 after four passes the profile is
  reset and the updates are damped by half;
* after 16 passes the stage is accepted as it is, **unless** its error is above 3 % **and**
  its load is above the largest load of the stages so far: then it is refused. So a stage
  that does not converge is kept when the load has fallen, which is the collapsed last
  stage of many of Response's shear responses;
* a stage whose state code is not zero (below) is refused while the multiplier is 0.5 or
  more, and one with code 3 is refused while its load is above the largest so far.

**A stage refused, or not solved.** The stage is reset to the one before and tried again
closer: the first time at half a base step back with the multiplier marked; after that the
multiplier is halved each time (and doubled again after a stage accepted at the first try
while it is under 0.25). When the multiplier is under 0.2 (0.05 if the control is the axial
strain) and the other control variable is not the present one, the control variable is
changed instead: the multiplier goes back to 1, the base step is that of the new variable,
in the direction the new variable has been moving over the last two thirds of the stages.
The response ends when the multiplier falls under 0.005 (without shear: after eight tries).

**The state code** of a stage [`004204b0`]. A node is *crushing* when its principal
compression is within 1.5 % of its (softened) strength or its principal compressive strain
is beyond ε0.

* 1: a node whose shear on the crack is at its limit with a zero in a field taken to mean
  no transverse steel there;
* 4: a transverse strain beyond the largest rupture strain of the transverse steels (10 mm/m
  at least);
* 3: the web crushing: a crushing node that carries shear and does not belong to the
  crushing zone that starts at an extreme fibre (top first, else bottom); or the whole
  depth crushing with shear; or every node beyond ε0;
* 2: an extreme fibre's principal compressive strain beyond 5·ε0 (10 mm/m at least);
* else 0.

**The end of the response.** After each accepted stage, in this order:

1. the state code is not zero and the load is under 0.8 of the largest so far: the end;
2. a new event against the stage before (as above): not the end;
3. the load is under 0.2 of the largest so far, from the eleventh stage on: the end;
4. with constant loads, a load that is being increased has fallen under 1 % of its largest
   value: the end;
5. at any node the principal compressive strain is beyond 4 times the largest ε0 of the
   concretes, or the transverse strain is above 50 mm/m: the end;
6. the strain at the top or bottom fibre is above 5 times the largest rupture strain of the
   steels: the end.

Besides: a stage with less than 1 % of the load of the one before is dropped; of three
stages in a row with no load, one is dropped; the response ends after 327 solves. The stage
Response shows when the solve ends is the one with the largest load.

## Inferred or fitted values, in one place

| What | Value | Basis |
|---|---|---|
| Stepping and end rules without shear | above | Response's control charts; they agree with the binary's rules as read |
| Largest number of layers | 220 | r2c's own; Response's limit was not read |
| Start of unloading tracking | stage 1 | one prestressed case (Cm4) |
| Stirrup plastic strain kept by depth | yes | one case (Newbeam, M/V = 2 m) |
| The two sides of a step in width kept apart | profile and stirrup ratio | r2c's own; Response's charts show both sides (I-girder) |
| A circle from Quick Define is its 13 rows, straight between | yes | one case (column, N alone) |
| "Not closed" global solution carried on from | out of balance under 2 % of the section's scale | r2c's own reading of Response's solve status |
| Damping under shear alone | half the update in the second half of the passes | one loading (shear alone) |
| Shear alone stepped in the shear strain | 0.02 mm/m; half under constant compression | two cases |
| "Large" constant axial load for the base step | above 0.1 MPa on the gross area | one case |
| State code 1 needs no stirrup at the node | yes | one case (no stirrups) |
| Factored steel capped at fy | yes | one case (CSA factors) |
| Shrinkage profile through more than three points | parabola through the nearest three | r2c's own reading of the manual; three points compared |
| Interlocking hoops are stirrups | yes | one case (column, M/V = 1 m) |
| Second starting plane and step cut-back for the initial state | above | r2c's own; three cases |

## Not implemented

Out of scope by the owner's decision: hollow sections, long-term effects, strain
discontinuity, the old text input format; and since 2026-11-22 draped tendons (D4) and the
Hsu softening models with Tamai tension stiffening (D5). Beyond the documented scope and
taken out on 2026-11-22 (D10, D18): compression softening 4, 16 and 17, and a segmental
curve for reinforcing steel. r2c refuses these as out of scope; what Response itself rejects
is an input error (`docs/scope.md`, section 3). Response's program folder is not read (D9).
