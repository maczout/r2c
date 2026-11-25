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

**Which control charts [O]**, by the load increment (N, M, V), as r2x captures them
(`export.control_keys`). With shear: shear against shear strain, then moment against
curvature when M increases, axial load against axial strain when N increases without M,
shear against axial strain otherwise. Without shear: moment against axial strain and
against curvature; when N increases together with M the first is axial load against axial
strain (the capture `newbeam-nm`); N alone, axial load against axial strain. In kg-cm units
a force on these charts is labelled "ton" [O: Newbeam in kg-cm units under axial load alone
and under shear, through r2x].

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
constant beyond the end points. With more than three points the program reads its table
three points at a time from the top down: a parabola through the first three, another
through the third to the fifth, and so on, and a straight line to a point left over
[B `004b6df0`, read 2026-11-24, step A-6; no case has more than three points, so nothing
compares it]. A bar layer's thermal strain
is taken off its prestrain [T, manual 3-5: "can be used the same way as prestrains"].

### What the concrete's offset does [B], read 2026-11-24 (step A-6)

Each node carries offsets: the strain the concrete would have unrestrained, along the
member and across it. The routine that makes the nodes sets them from the section
(`004a9d90`, through `004ff8f0`): along the member the sum of two tables over the depth,
across it one of the two alone. The one in both is the shrinkage and thermal profile; the
other was taken to be the strain discontinuity, which is out of scope (inferred: it is
empty in every case here, and Response's Transverse Strain chart under a thermal profile
is that profile). So in r2c the offset is the same strain εsh(z) in both directions. Four
things follow, all read, and all without effect where εsh is nothing:

* **The node** (`0046aaa0`). The concrete's strains are the node's less the offsets, εx − εsh
  and εy − εsh; angle, principal strains and stresses come from those. The principal
  strains the node keeps, and the charts show, are the whole strains: the concrete's own
  plus the offset in that direction (the same εsh). The Longitudinal Strain and Transverse
  Strain charts show the whole strain too. r2c: `Detail.sh`, added back in `export`.
* **The transverse strain is solved for, also without shear** (`004a8b20`). The test for a
  node with next to no shear strain (below) fails where the node has an offset: the sizes
  of its four offsets (along, across, and in the two principal directions) must come to
  under 10⁻⁶. Such a node goes through the transverse solve: concrete on εy − εsh, stirrups
  on the whole εy, no total stress across the member. A new node starts from εy = εsh. So
  under a thermal gradient the stirrups are stressed with no shear on the section
  (newbeam-thermgrad-m at cracking: 46 MPa at their top end in Response and in r2c).
  r2c: `Analysis.eval_nodes` and `transverse`, whenever the section has a profile.
* **The flexural tension zones are those of the concrete's own strain** (`00441d80`, with
  `004bb0d0`). From a face whose own strain εx − εsh is tension the program walks over the
  depth, from one height to the next at which the profile is given (and at which a second
  table over the depth has a point: taken to be the outline's, inferred; on a rectangle it
  cannot matter), and puts the zone's axis where the own strain changes sign, on a
  straight line between the two heights. With a curved profile the axis is therefore not
  where the own strain is nothing: under the thermal gradient of the set, at cracking, 42
  mm above mid-depth where the parabola's zero is 65 mm above (estimated from Response's
  strains at that stage). Without a profile this is the neutral axis, as before.
  r2c: `Analysis._net_axes`. With shrinkage of 0.4 mm/m the zone begins 57 mm higher
  than the neutral axis at the stage the bars yield, and the limit of the concrete's
  tension over those 57 mm is the zone's and not three times the tensile strength
  (measured: Principal Tensile Stress there 1.1 to 1.4 MPa before, Response's 0.05 to 0.4).
* **The cracking strength over the depth counts the restrained strain as a prestress**
  (`00423e50`, `004b5770`). To the force and moment of the prestressed bars the routine
  adds those of the profile as if fully restrained: a straight line is fitted by least
  squares to the points given (not to the curve: the points, unweighted), and its value
  at the centroid times the area, and its slope times the inertia, each times the
  concrete's stiffness, are added. Heights from the centroid of the gross concrete [O:
  with that origin the limit line of the thermal case's Principal Tensile Stress chart at
  cracking is Response's to the fourth decimal, 2.4607 MPa at the top and 2.9973 at the
  bottom; from the transformed centroid it is 0.4 % off, from the bottom 18 %]. The
  routine does the same with a second table, taken to be the strain discontinuity (out of
  scope). r2c: `Section.cracking_table`.

*The first envelope of the Transverse Strain chart* [O, with B `004a9d90`]: at the first
stage the envelope ("The shear charts" below) starts from the straight line between the
offsets at the two faces, not from nothing: under the thermal gradient the upper line is
straight from 0.3 mm/m at the top to nothing at the bottom, the lower one the parabola.
r2c: `export.envelope`.

*Not cloned:* the program's transverse solve stops at a tolerance, and in the shrinkage
case its stirrup stresses at the nodes of the compression zone differ by up to 0.6 MPa in
59 where the solution is the same at every node (r2c: −59.06 at each). The Transverse
Average Bond chart, which is the difference between neighbours, shows 0.05 to 0.07 MPa
there on a chart of 1.06 (6.1 %, a Should check at the last stage: `docs/summary.md`, D75).

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
  probes]. A horizontal tie (7) is solved as a stirrup and shows no transverse bond: with
  ties alone the bond chart is zero [O: the probe newbeam-pattern7 through r2x, 22 of 23
  charts byte for byte those of a stirrup, the bond chart zero]; with ties and stirrups
  together the stirrups' bond is drawn as without the ties [inferred]. Of several sections
  in one file the first is read [O: Response opens the first; its sample files].
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

### The longitudinal reserve over a tension zone [T 4-5; B `00441d80`, `00440400`]

The limit f1cx is a profile over each flexural tension zone, from the neutral axis to the
face (`Analysis.crack_check`; read in increment A2, the factor's place in step A-5). The
bars crossing the zone give it a capacity moment about the axis: each bar's reserve at a
crack times its area and its distance from the axis. That moment is set against two
moments of the concrete in the zone: Ma, a uniform tension of 0.6·ft, and Mb, a further
tension rising from nothing at the face to 2.4·ft at the axis.

* Capacity up to Ma: a uniform limit, the capacity moment over the zone's first moment.
* Between Ma and Ma + Mb: 0.6·ft at the face, rising linearly to the axis by what the
  capacity has over Ma.
* Over Ma + Mb: 3·ft at the axis, and at the face 0.6·ft plus what is left over.
* A zone no bar crosses has no capacity moment and a limit of nothing (D30).

**With material factors** [B `00440400`, read 2026-11-24, step A-5]: the limits at the face
and at the axis (0.6·ft, 3·ft) carry the concrete's factor, but Ma and Mb are summed with
the unfactored ft. So with the CSA factor of 0.65 the uniform branch reaches further than
its own face value: where r2c had a sloping limit from 0.76 MPa at the face, Response has
a flat 0.83 MPa (Newbeam with CSA factors under M, last stage: the limit line of the
Principal Tensile Stress chart 11.3 % off before, 0.0 % with the rule).

### A node with next to no shear strain [B `004a8b20`, `004a7b60`], read 2026-11-23 (step A-2)

Before Response solves a node's transverse strain (`004a8b20`) it tests the
node (with or without shear; without shear and without shrinkage every node passes, and
r2c then solves no transverse strain at all): if the size of its shear strain is under two millionths of the difference of its
longitudinal and transverse strains (each less its shrinkage or thermal strain), plus
10⁻¹⁰, and the node has no shrinkage or thermal strain (the sum of the sizes of its four
strain offsets under 10⁻⁶), and a value read from a table over the depth that the analysis
keeps is under 1 in size, the node goes through a second routine (`004a7b60`) in place of
the transverse solve. That routine takes the node as uniaxial: the transverse strain is the
node's transverse offset (nothing, with no shrinkage), the principal directions are the
member's, the concrete's stress and cracking are found from the longitudinal strain alone,
and **the stirrups are left out: the node's stirrup stress, its stirrup stress at a crack
and its stirrup ratio are set to nothing.**

For stirrups with no prestrain this cannot be seen: their stress at such a node is next
to nothing anyway. With prestrained stirrups it can: the Stirrup Stress chart shows
nothing at such a node and the prestress at its neighbours. Under no load every node is
such a node; near a face, where a node that carries no shear has a profile value of a few
millionths (the update adds 10⁻⁶ in each pass, "The shear strain profile between
passes"), a node falls on one side of the test or the other from stage to stage. Measured
on Response's capture of Newbeam with a prestrain of 1 mm/m on the stirrups at M/V = 1 m:
at stage 0 all 19 nodes within the stirrups show no stress; from stage 13 to 28 three to
ten of the nodes 0.4 mm apart at the bottom end of the stirrups do, a different set at
each stage, and Response's own Transverse Average Bond chart at that end goes with it
(0.13, 18.6, 37.2, 1.4, 37.3 MPa … at successive stages).

r2c (`Analysis.lone_nodes`, in `Analysis.detail`): the test is made on the state a stage
reports, with r2c's solved transverse strain in it, and at such a node the transverse
strain, the stirrup stress and the stirrup stress at a crack are reported as nothing and
the node counts as one with no stirrups for the bond chart (below). **Not taken over:**
the forces are not evaluated differently at such a node (the stirrups carry no part of
the axial load or the moment, and the transverse strain r2c solves there is the 0.012
mm/m of the prestress at most) [O: with the rule in the reported state alone no check on
the 29 cases moves but the two it was written for]; the table over the depth in the test
was taken to hold nothing in every case here (inferred: no input of the manual was found
to fill it); the offsets are the shrinkage and thermal strains (read in step A-6: "What the
concrete's offset does"). Which nodes near a face fall under the test at a given
stage is not Response's node for node: it hangs on a profile value of millionths.

Tables over the depth [B]:

* longitudinal and transverse crack spacing: "Crack spacing over the depth", below;
* the bond parameter M (100 stations): from the bars' perimeters within 7.5 db, falling to
  nothing one crack spacing away; M = 3.6·b·s/(π·db·legs) for stirrups; the lesser governs;
* the steel ratio for the strain concentration of stirrups at a crack (100 stations).

### Crack spacing over the depth [B `0043f570`, `0043faf0`, `0043e8d0`, `00440100`, `0043f0d0`], read 2026-11-22

Response makes each spacing as a table of points over the depth and reads it linearly
between them (`004b6a30`); `0043fa20` makes both when the section is set up. A spacing
the user gives is used as it is, at every height.

**Longitudinal** (written, off: see the end of this section).

*A layer's term* [`0043f570`], the 0.1·db/ρ of the CEB expression. Every layer counts
with a weight that is its area at the layer's own height and falls linearly with
distance to nothing at 15 of its own diameters. db is the mean diameter by those
weights; ρ is the weighted area over the concrete between 7.5·db above and below the
layer, within the section. A layer outside the section has a term of 0.1 mm.

*The spacing at a height* [`0043faf0`]: for the nearest layer at or above and the nearest
at or below (not one on the top or bottom face),

    s = √((2·d)² + (b/n)²) + the layer's term,

d the distance in height, b the width at the layer on the side that faces the height, n
the layer's bars and those of every other layer within one bar diameter of it in height.
The lesser of the two, no more than five times the depth (which is also the value where
there is no layer) and no less than the aggregate size held between 2 and 25 mm.

*The points* [`0043e8d0`]: every layer and every corner of the outline, and 0.1, 0.25,
0.5, 0.75 and 0.9 of the way from each of those heights to the next one down. The node
takes the table's value, never more than the depth [O: Newbeam's chart stands at 600 mm
where the expression gives 680].

**Transverse** (in use since 2026-11-22).

*The spacing at a height* [`00440100`], on one side of the height where the width steps:

    s = √((b − 100 mm)² + sv²) + 0.1·db/ρv,

over the stirrup types that reach the height: ρv the sum of Av/(sv·b), db and sv each
type's value over the number of types. A hoop's Av/(sv·b) is multiplied by the cosine of
the angle whose sine is the height above the hoop's middle over its half height (plus
0.1 mm). Five times the depth where no stirrup reaches, at the bottom face and where
there is no width; no less than the aggregate size held between 2 and 25 mm.

*The points* [`0043f0d0`], for each part of the outline from the top down: its top (the
first part), or where the width steps from the part above, the lower side of the step,
0.1 mm under it if the section widens there; one stirrup diameter above and below the
top end and the bottom end of each stirrup that ends inside the part, held inside the
part; its bottom, or 0.1 mm over it where the part below is narrower by more than 10 mm.

**Checked against Response's charts** (measured, `python tools/spacing.py`): the two
tables give Response's Longitudinal and Transverse Crack Spacing charts within 0.001 mm at
every node on the circular column, the T-beam and the I-girder, but for one node of the
transverse chart at a step of the I-girder (1.4 mm in 1369). Before, r2c's tables were
21 and 11 % off on the column and 6 to 8 % on the T-beam: its longitudinal spacing took
the bars of the layer alone and all the steel within 7.5 db unweighted, on 100 stations;
its transverse spacing had no factor for a hoop and a jump, not a ramp, at a stirrup's
end.

**Not read in full:** both routines branch on a setting of the section (the field at
`0x338`; the branch that fits the charts is the one for the value 1) and, in the other
branch, on a number each layer carries (at `0x97`: there a layer's weight is divided by
it, and a layer with 100 or more does not count). What the setting is was not found; no
phase A case takes the other branch as far as the charts show.

**Both tables are in use.** The longitudinal table was written in step A-1b and switched
on in step A-1c (owner, 2026-11-22, D46); r2c's earlier longitudinal table is gone.
Measured on the 24 cases against the run of record of step A-1b (2026-11-22,
`tools/changes.py`): 43 checks came inside, among them every check of longitudinal crack
spacing; the Could views went from 15 to 20 of 24 cases; the last-stage point of "constant
N +200 kN, then M" (D35) came inside (6.2 to 1.4 %). Seven went outside and are known
deviations by D46 (`docs/status.md`, "Known deviations that came with the longitudinal
crack spacing table"): the rising branch of M/V = 0.5 m (2.7 to 9.9 %: r2c's last stage,
after its own peak, which falls back to a point nearest to Response's fall of load before
the peak; Response's own rising points stay within 2.7 % of r2c's curve); transverse bond
at the peak of the I-girder with shear (2.5 to 49.8 %, and that case's Should views with
it) and of M/V = 2 m (3.7 to 22.5 %), a spike at the end of the stirrups in a stage of
r2c's own that has not converged; two views of M/V = 0.5 m by a point; the post-peak of V
alone (3.7 to 6.9 %).

### At a step in width [O]

Where the width steps (web to flange) the shear stress and the shear strain jump with it, and
the node above and the node below the step are different nodes at one height. Response's own
charts show the same: three points 0.05 mm apart at each step, the shear strain a quarter
across a step to four times the width (measured, I-girder, M/V = 2 m). In r2c:

* the shear strain profile has a point on each side of every step, and a layer's node on a
  step reads the profile on the layer's own side;
* a node's stirrup ratio ρv = Av/(b·s) is taken with the width of the node's own layer.

Both are r2c's own way of keeping the two sides apart, not rules read from Response. Since
2026-11-22 they apply only to a step of 10 mm or less: at a larger one Response's thin layer
is there ("Layers", "Across a step"), with a point of the profile at each of its faces. The
transverse crack spacing has a point on each side of a step since 2026-11-22 ("Crack
spacing over the depth"); the bond parameter and the steel ratio at a crack are still
interpolated across a step from their 100 stations.

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
leave a layer thinner than h/2048 or the edge is within 0.2 mm of a boundary.

*Across a step* [B `00434eb0`], since 2026-11-22 (step A-1). Where one stretch of the
outline ends and the next begins with a width more than 10 mm different, or with another
concrete, the boundary between them is replaced by two: 0.05 mm above the step and 0.05 mm
below it. So a layer 0.1 mm thick lies across the step, its top node on the upper stretch,
its bottom node on the lower one and its middle node on the step itself; the other
boundaries of the two stretches stay where they were. The layer is too thin to be split.
The middle node has the width, and the shear strain, of the wider side [O: Response's
Shear Stress and Shear Strain charts on the I-girder at both of its steps, 4.0 and 3.0
times less at the middle node than at the web's node, the ratios of the widths; one
section]. r2c: `Analysis.thin`, `_initial_bounds`, `layer_nodes`, `profile_z`
(`solver.own_thin_layer`). Before, r2c had one boundary on the step and kept the two sides
apart in its own way ("At a step in width"), which stays for a step of 10 mm or less.
Measured: r2c's nodes at the two steps of the I-girder are Response's (333.16, 333.11,
333.06 and −316.84, −316.89, −316.94 mm); the T-beam under −M, steel stress at a crack at
the last stage, 100 to 0.0 % (the concrete's moment over the cracked halves of layers
changes with the layer at the step); transverse bond in Response's own states on the
I-girder with shear, 99.8 to 0.0 % at the stage before the peak (the jump of the stirrup
stress at the web's edge is spread over the thin layer, not over half a web layer).
Not checked: a change of concrete at one width (no case).

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
by the shear stress [O]. The longitudinal bond chart is the change of bar force along the
member over the bar surface.

### The shear charts [B], read 2026-11-22 (increment A4)

The chart data are filled by one routine (`00480590`, reached from `004837e0`); nothing is
calculated when a chart is drawn except as said here.

*The envelopes behind the Shear Strain and Transverse Strain charts* [`0041b1d0`, called
once when a stage is accepted, from `00418af0`]. Each stage has its own: at each of its own
nodes, the larger (upper line) or smaller (lower line) of its own value and the envelope of
the stage it followed, read linearly at that height. The first stage starts from zero. A
stage set aside while an event is closed in on was made before the stages put in between,
and is not accepted a second time: those stages never enter its envelope, nor any later
one. r2c: a stage records the stage it was solved from (`Shear.run`), and
`export.envelope` builds the lines. Before, r2c drew the running extreme of every stage in
order. Measured on M/V = 1 m: Response's envelope at stage 11 is that of stage 3 with its
own profile (stages 4 to 10 were put in between); the reading fits every stage of the 20
captures with shear in the archive within the printed precision.

*Shear on Crack* [`00480590`]. The node's value with its sign (r2c drew its size). The
limit is drawn once the larger of the largest positive and the largest negative value over
the depth passes 0.001 MPa: on the side of the larger of the two, and on the other side as
well when that side's extreme is over a fiftieth of the larger. The negative line is minus
the positive one. Where a chart's values are within a few thousandths of a MPa the two
programs can fall on either side of that rule, and one draws a line the other does not
(two phase A stages; `docs/summary.md`, D38).

*Transverse Average Bond* [`0047fcd0`; the factor `00485640`, the window `00484420`]. A
table over the depth is made first: for each half layer, the change of the average stirrup
stress between its two nodes over their distance, as a size, times the stirrups' area over
their perimeter (for one bar type the area of a bar over π times its diameter; taken at
the layer's bottom node, so nothing where that node is beyond the stirrups); zero unless
there are stirrups at the layer's top and middle nodes. Each value is put at the top of its
half layer and the table is read linearly between. The chart is that table averaged over a
window at 41 evenly spaced heights: five stirrup diameters long, at most an eighth of the
depth, a twentieth of the depth where there are no stirrups, cut off at the faces. r2c:
`export.bond_table`, `export.bond_window`. Before, r2c drew a numerical derivative of the
stirrup stress. Measured: from Response's own stirrup stress chart the rule gives its bond
chart within 0.01 MPa at 469 of 470 stages of the nine phase A captures. Not checked with
more than one stirrup type or with stirrups over part of the depth (one parked case moved
far: `docs/status.md`).

*"Stirrups at a node", corrected 2026-11-23 (step A-2)* [`004a80e0`, `004a7b60`]. The
test is on the node's own stirrup ratio, which the stirrup routine sums over the stirrups
whose depth holds the node, and which is nothing at a node with next to no shear strain
("A node with next to no shear strain"). r2c had read the ratio from its table over the
depth, which gives a little just beyond the stirrups' end; a prestress that stops at the
end was then taken for a change of stress along the stirrup (18.6 MPa of bond at the top
end of the prestrained stirrups, where Response's chart has nothing). Measured with
`python tools/bond.py CAPTURE`, which applies the rule to a capture's own Stirrup Stress
chart: on Response's capture of the prestrained stirrups the chart at the peak was 355 %
off before the correction and is within 0.4 % at every stage after it; on five Newbeam
captures with shear, on the column with shear and on the column with interlocking hoops
it is within 0.8 % at every stage whose chart reaches 0.01 MPa (the rule had not been
checked on a hoop before), but for M/V = 0.5 m, 17.9 % at one stage.

*Average Angle: one rule not taken over* [`004a9d90`, its end]. After the angles are found,
Response turns some of them by 180°, by a test on the mean angle of the nodes made first
(the base nodes, before layers are split): nodes made later keep an angle near 180° where
the shear strain is next to nothing and negative, and r2c draws 0°. Seen at two nodes at
the peak of M/V = 2 m. r2c does not keep its nodes in the order Response makes them, so
this was left (`docs/status.md`).

### The history of the stirrups [B `0041e310`, `004a9d90`, `004aea40`], read 2026-11-22: written, off

Response keeps the plastic strain of the stirrups as a table over height that belongs to a
stage: written when the stage is accepted, from the stage's own state at its own nodes
(strain less stress over modulus), in place of the table it had; a new stage starts from
the table of the stage before it and reads it linearly at its own nodes. A stress above the
unloading line through that plastic strain is brought down to the line, not below minus
the yield stress; in compression there is no line. With two or more stirrup types Response
keeps no history. r2c keeps the largest plastic strain so far on the fixed heights of its
tables (about 6 mm apart on Newbeam) [O], which near a sharp change over the depth gives a
plastic strain that is too large beside it: in Response's own states at the last stage of
three cases the stirrup stress is then up to 94, 93 and 143 MPa off, and within 3, 16 and
10 MPa with Response's table [measured, 2026-11-22, a copy of r2c outside the repository].

**Response's rule is in the kernel and off** (`Analysis.own_stirrup_history`;
`docs/summary.md`, D39). With it on, on the 17 cases: the peak of "N constant, then M + V"
comes inside (shear stress 15.5 to 1.3 %, transverse bond 6.1 to 0.3 %) and four checks at
the fall of load of M/V = 0.5 m; but **the rising branch of M/V = 0.5 m goes outside (3.7
to 7.6 %)**, with six other checks on M/V = 0.5 m and 2 m. Keeping the largest value at the
same heights in place of replacing gives the same results, check for check. Not taken over
in either: the stress at a crack on the same line, the factor for wide spacing on the
average stress, and the prestrain inside the plastic strain (none of them at work on
Newbeam).

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
31), and 2 to 5 % on Liping LB1 from stage 13. The first of these is explained since step
A-5 (the slopes of the compressive stress, below); Liping LB1 is refused since D23 and was
not looked at again.

**The slopes of the compressive stress [B `004ac960`, called from `0046b940`], read
2026-11-24 (step A-5): written, off** (`Shear.own_slopes`, `ConcreteLaw.compression_slopes`;
`docs/summary.md`, D69). Until now r2c took the two slopes along the principal compression
as differences of its own stress relation. The program has them in closed form, and its
form is not everywhere the relation's slope:

* *Against the compressive strain, softening held:* the slope of the base curve's shape at
  ε2 over the strain at peak stress, times the lowered peak stress. Popovics: the exponent
  n = 0.8 + β·fc′/17 and k = 0.67 + β·fc′/62 (1 before the peak, and never under 1) are
  those of the lowered strength, with no lower bound on n here; the slope is divided by the
  unlowered ε0 also for the models that lower the strain at peak stress (9, 14, 15 and 1,
  11), so it is β times the relation's slope there. Model 3 (Vecchio-Collins 1992-A): on
  its plateau the curve is taken at its peak, with the unlowered n; past ε0 the unlowered
  curve, with β applied twice. Parabola: the tail past the lowered peak strain for models
  1, 9, 14 and 15 (not 11). Linear and elasto-plastic: 1/εp up to the peak, then nothing.
  Segmental: the table's slope.
* *Against the principal tension, through the softening alone:* the curve's shape times
  fc′ times −dβ/dε1, with dβ/dε1 the slope of the model's own formula, and nothing where β
  sits at a bound (1; 0.8 for Mehlhorn; 0.65 and 1 for Maekawa). **Nothing at all for the
  models that soften by a ratio or sum of the two strains (1, 3, 11), for Noguchi (8) and
  for "none".** The change of n, k and of the strain at peak stress with β is left out for
  every model (with the default at 60 MPa that makes this slope about a sixth larger than
  the relation's). For Vecchio-Collins 1992-B (5) the program's expression is
  (1 − 0.27/ε0)/d², d = 1 + 0.27·(ε1/ε0 − 0.37): the sign is the other way from the
  formula's slope and a 1 is added to 0.27/ε0. Taken over as read; set against Response's
  own figures on that girder the read form fits (0.7, 0.6 against 0.8, 0.6 % at stages 33
  and 34) and the formula's slope does not (1.1, 1.4 %).
* The slope against the tension is counted with the ratio of the change of ε1 to that of
  ε2 that the column brings (tan²θ for the longitudinal strain, 1/tan²θ for the
  transverse), and with nothing for the shear strain: the routine is called with −1 there
  and takes a negative ratio as none. (This is the rule already recorded above, now with
  its place.)
* A principal "compressive" strain that is tensile (over −1e-9) takes the tension side of
  the same routine; r2c keeps its difference there, which is that slope.

Measured with `python tools/flowset.py ARCHIVE --inputs …` (2026-11-24; r2c in Response's
own state at every stage of every shear capture, 46 cases, 2,007 stages at which Response's
own calculated line is within 2 % of its state): r2c's calculated shear stress is more
than a point further from the state than Response's own at **309 stages with the
differences and 80 with the program's slopes**. By case: the I-girder with softening 3
(Vecchio-Collins 1992-A) 14 to 1, the worst excess 11.6 to 3.5 points; with the default
softening at M/V = 2 m 13 to 1; Hsu-Zhang 44 to 1; M/V = 0.5 m on Newbeam 11 to 0, which
is the difference "after a fall of load, on the recovery" left unexplained on 2026-11-19;
the two cases in US units at M/V = 1 ft 18 and 17 to 0. Every case's one stage left is its
first (a shear of 2 kN on the I-girder). What is left after it: Maekawa (7) 40 stages, at
1.5 to 2.0 % against Response's 0.5; Mehlhorn (6) 10; Porasz-Collins (13) 7. Not looked
into (one approach, D68).

Why it is off: on the 38 cases 27 checks come inside and 5 go outside, and one of the five
is a Must, the shape of Newbeam with elasto-plastic tension stiffening
(`docs/verification.md`, "Step A-5"). The no-regression bound keeps it off until the owner
decides (D69).

## The state under the constant loads [T 7-3; O]

The first load stage is the state under the constant loads alone. It is found by Newton
iteration on the strain at the centroid and the curvature, each step cut back until it
lowers the residual (a section cracked by its own shrinkage or prestrains has a kink there).
It starts from the unstrained section, and if no state is found from there, from the plane
that fits the section's own strains: the shrinkage profile, then the strains at which the
prestrained bars carry nothing [T 7-3: with shrinkage the first estimate is "a linear fit to
those profiles"; the second plane and the cut-back are r2c's own].

Under a constant moment, if no state is found from those, the search starts again from
cracked planes: a strain difference over the depth of 0.25, 0.5, 1, 2, 4 and 8 mm/m, bending
either way, with the centroid at 0.15 of that difference in tension [O: r2c's own, since
increment 2. A moment above the cracking moment has no way from the unstrained section
that brings the residual down across the fall of force at cracking: Newbeam under a
constant 50 kNm was not solved; Response's first stage there is a cracked state].

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
`004a9030`). **The secant, under a stepped curvature, is in use since increment A4**
(owner, 2026-11-22, D35; `Flexure.own_curvature`): it brings M's last stage inside and
leaves one point outside at the last stage of "constant N +200 kN, then M", a known
deviation (`docs/status.md`). **The general solve, under a stepped axial strain, is written
and not in use** (owner, 2026-11-22, D36: tension's shape is a known deviation for phase A;
`Flexure.own_axial`); there r2c's own solve (the balanced state, to a root of the unbalanced
force) is still what runs.

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
(the 10 % growth seen on the control charts); at which moment, below.

*When the base step grows* [`00418860`, the wrapper of the pass routine; `00418af0`,
`0041a870`], in r2c since 2026-11-24 (step A-4; `Shear.late_growth`). The test (from the
fifth stage, multiplier not above 1, Δ0 under a tenth of the target) is made before
every pass on a stage, with the target as it is at that moment, and a new stage's target
is set inside its first pass. So: after a stage is kept, Δ0 grows from that stage's
target and the next target follows from it, as before; **a first try that fails in its
first pass leaves Δ0 as it was**, and one that fails later has grown it from its own
target; a further try grows Δ0 from the target it was given when the try before failed.
Until now r2c grew Δ0 from a new target before the first try at it. [O, seen in the
program's own values, `python tools/rtrace.py`: with a tension stiffening factor of 0.5,
after the stage at 4.6797 rad/km the try at 5.1477 fails in its first pass with Δ0 at
0.4680; the next tries are at 4.8925 with Δ0 0.4892, then 4.7701 and 4.7090. r2c had
0.5148 and went to 4.7638 and 4.6994. With elasto-plastic tension stiffening the first
try runs its 16 passes, Δ0 is 0.5148 and Response's own tries are at 4.7638 and 4.6994.]
No check changes on the 37 cases (`tools/changes.py`): r2c's failing tries do not fail
in the same pass as Response's (below), so the rule alone moves no stage onto
Response's.

**Events.** After a stage is accepted it is compared with the one before: newly cracked
(principal tensile strain above the cracking strain at any node), newly crushing (principal
compressive strain beyond ε0 at any node), a node state of yield or slip at a crack (only
where there are no stirrups), a change in the number of ruptured layers. If there is one,
and the last step is more than 2 % of the travel of the control variable from the start
(0.5 % for crushing, 1 % for rupture), the last stage is set aside and a stage is put at a
fifth of the way to it (four fifths, for a stage that has un-cracked); this repeats on the
shrinking interval, and then the stage set aside is taken up again.

*"Cracked", for an event* [`004181d0`, `004ff4e0`]: the cracking strain here is the node's
own before it is lowered for the compression across the node ("Cracking under
compression": `004ff4e0` is the first lines of `0046a960`, the cracking stress of the node
over Ec and no less than the concrete's own cracking strain, without the factor k). So a
node that has cracked under compression, below that strain, is cracked in the node and
does not yet make the stage a cracked one. In r2c since 2026-11-22 (step A-1b); before, a
stage counted as cracked as soon as any node had. [O, measured: under V with a constant
compression Response closes in between the shear strains 0.178 and 0.197 mm/m, with
stages at 0.182 and 0.185; r2c closed in between 0.163 and 0.179 with seven stages
Response does not have, and now has its stage at 0.183. `python tools/stagematch.py`: r2c's
stages up to the peak 30 to 24, Response's 25.]

**A stage put in between** [`00415e30`, `00416730`, `00418af0`], in r2c since 2026-11-22
(step A-1b):

* its first estimate is the three global strains of whichever is nearer in the control
  variable, the stage before or the stage set aside, with the control variable at its
  target (`00416730`; for a stage that is not put in between, the strains of the stage
  before: the extrapolation written there multiplies by a difference that is zero);
* the shear strain profile it starts from is that of the stage set aside where that
  stage has un-cracked, and of the stage before for every other event (`00415e30`);
* if it is refused or not solved it is dropped. The stage set aside is then taken up as
  it was found and is marked: the event is closed in on no further (a field of the stage
  that every new stage has set and only this clears). The step multiplier and the count
  of tries are left as they were (`00418af0`);
* a stage set aside and taken up again is not solved again.

[O, measured: on the I-girder at M/V = 2 m (parked cases) Response's stages around the
closing of the top cracks are at curvatures of −0.539, −0.533, −0.532 and −0.530 rad/km
with moments of 49.6, 51.8, 32.6 and 34.5 kNm; r2c's are now 49.5, 51.8, 32.5 and 34.4 at
the same places. Before, r2c had 49.5 at −0.539, 51.1 at −0.532 and no stage at −0.533:
its stage at −0.532 started from the cracked stage before and stayed cracked.]

**Seen since, on the captures (step A-3, 2026-11-23) [O].** Whether Response keeps the
stages it puts in while closing in on an event is not the same from run to run. On this
girder at M/V = 1 m the web cracks between the curvatures −0.251 and −0.171 rad/km
(shears of 366 and 463 kN). In three captures of five Response has ten stages there,
each a fifth of the way on, and r2c has the same ten; in the other two, the fixture
among them, it has none. The parked case with Collins 1978 softening does the same (one
capture of four without them), and with softening 16 at M/V = 2 m one capture of four
lacks one of the stages put in where the top cracks close. So "nothing in between" at
the web cracking, in the paragraph below, describes one of Response's two variants and
is not a deviation of r2c's; the stage at −0.539 is in none of the 13 captures at
M/V = 1 m and remains open. Inferred from this, not read: a stage put in between takes
something from the run that the input does not fix. `python tools/repeat.py`.

**The same girder at M/V = 1 m (D43): seen 2026-11-24, see "What the running program
shows" below.** Response does try the stage at −0.539, its solve gives up in the first
pass on a section it takes to have next to no stiffness, and the stage is dropped. The
paragraph that follows is the record of what was ruled out before that was seen. There
Response has no stage at −0.539 or
−0.533: it goes from −0.571 (cracked) to −0.530 (un-cracked), and later from −0.251 to
−0.171, where the web cracks, with nothing in between. By the rules above it must have
put a stage in between at both places and dropped it, which needs that stage to be
refused or not solved. r2c solves both (the cracked state at −0.539 in five passes; the
un-cracked one at −0.235 in one) and keeps them, so its curve has the fall of load
Response's has not. What was ruled out, each by reading and by trying it: the closing-in
test (`00419ff0`: 2 % of the travel, as written above); the mark on the stage (set by
`00433c50` on every new stage, copied by `004330a0`, cleared only in `00418af0`); the
global solve (`004276a0`, below: r2c's writing of it finds both states in two to four
steps, at M/V = 1 m and 2 m alike); the state code (0 for r2c's two states); the refusal of a stage
that has not converged (its load is under the largest so far). Read since, in
step A-1c, and also ruled out: the 3 × 3 solve `004688b0` and its fall-backs `00467f20`
("When the profile update reports a stage as not solved", below: it takes a section with
no stiffness against shear at all, which this state is not); the state code on every
pass (0 on each of the five); the largest load so far while a stage is set aside (it is
kept, so a stage that has not converged there would not be refused for its load); the
step factor of the global solve; the profile update itself. With all of these written out
and switched on r2c still solves that stage in five passes and keeps it. **Not read:** what
the forces routine `004a9d90` does differently between its iteration mode and its final
mode beyond the steel stress at a crack (`004440d0` against `00442e50`); the assembly of
the right-hand side (`004252c0`, `00422570`), which was taken as read in 2026-11-19; the
iteration counter and the first lines of `004276a0` before its loop. One thing sets
M/V = 1 m apart on this girder and was not followed up: its depth is exactly 1 m, so
every test of M/V against the depth in the program (`00419250`: the base step halved
where M/V is under the depth) is decided by the last digit of the depth as the program
holds it.

**What the running program shows (step A-4, 2026-11-24) [O; B where an address is
given].** Response's own tries were read from the program as it ran, on 16 cases
(`python tools/rtrace.py`: the values of the stage control at every pass), and set
beside r2c's (`python tools/tries.py`). Up to a first difference r2c makes Response's
tries one for one: the same targets, kept and failed alike, mostly the same number of
passes and a profile error within a few tenths of a per cent. The first difference is
one of three things, and after it the two responses are on different paths:

* *Response's solve of the global strains gives up where r2c finds a state* (seven of the
  16). Its steps are whole Newton steps with no search along them (`004276a0`): near a
  limit point they overshoot, the shear strain is driven negative and the section is
  left with no stiffness. r2c's own solve finds the state, or runs its 16 passes. The
  stage the I-girder at M/V = 1 m "must have dropped" (the open item above, D43, D48) is
  this: at −0.5385 rad/km the stage put in between is not solved in its first pass and
  is dropped, exactly as the rules say. The same on two parked I-girders (softening 9
  and 14).
* *The depth range with stiffness is a stored value of the stage* [`00427cd0` reads it
  at +0x148 and +0x150; `00440ea0` sets it; `004190a0` copies it from the stage before
  after a failure], and the first step of a solve can be taken on a range left by an
  earlier evaluation. Where concrete has crushed inside the depth with both faces sound
  the routine leaves a hundredth of the depth about the axis (r2c: nothing). On that
  range the 3 × 3 stiffness is singular, the step routine gives up and the try fails
  without having moved. Seen at the dropped stage of the I-girder, and twice with the
  factor 0.5, where the try after a solve that broke down fails "at once" (4.8925 and
  4.7090 rad/km) although the state exists; r2c keeps a stage at 4.6994. It is not a
  rule that can be stated from the input: over the 16 cases a try after a failed solve
  fails at once in 2 of about 60. Not taken over.
* *A stage that has not converged after 16 passes is kept by one program and refused by
  the other* (four of the 16; and once, under V alone, Response keeps a stage 617 % off
  where r2c finds no state), because its error falls on the other side of 3 % (4.4
  against 1.1 %; 3.0 against 9.5 %) or its load on the other side of the largest so far
  (219.95 against a peak of 219.30 in Response; 217.40 against 219.64 in r2c). Such a
  state is where the sixteenth pass happened to leave it.

Of the other four, two are continuous differences that shift every later target by a
few thousandths (the state under the constant loads, "M constant, then M + V"; the shear
strain of a stage that has not converged, from which the first target after a change of
control variable is taken, the column), and two were not looked into (softening 12, at
its fourth try; M/V = 2 m, where the traced run is not the capture's). Also seen:
on a flat peak Response solves the same target more than once (the factor 0.5: stages
35, 36 and 37 are all at a shear strain of 3.9638 mm/m, with loads of 193.19, 193.46 and
193.19 kN; the peak is the middle one). And run under the tracer, which only slows the
program down, two cases gave another number of stages than in their captures (M/V = 2 m:
80 for 88; V alone: 53 for 52): what Response does at such tries depends on something
besides the input, timing among it [inferred; the stage control runs one pass at a time
from the program's idle loop].

The pass routine's tests were set against the listing once more [`00418af0`]: one was
not on record. Under control of the shear strain, from the twelfth pass, a stage whose
top or bottom fibre is within a fifth of its cracking strain is kept as it is once its
error is under 50 % [`004156b0`]. Not in r2c; no traced case shows it deciding a try.

### The global solve with shear [B `004276a0`, `004267c0`], read 2026-11-22: written, off

Response's solve of the three global strains of a stage, the same routine as the general
solve without shear ("The stage solve without shear"). The load factor is read off the
load that goes with the control variable (N for the axial strain, M for the curvature, V
for the shear strain; the first control variable's where that load is not increased). The
other two loads' unbalance is the right-hand side, the stiffness is the section's 3 × 3
(`00427cd0`, the one of the shear flow calculation) with the control variable's own
diagonal term multiplied by 10⁹, so that it stays where it is, and a strain is left out of
the step where its diagonal stiffness is under a ten-thousandth of the control's
(`004267c0`). Steps times a step factor ("The step factor of the global solve", below), no search along the step,
and no account of the load factor changing with the strains. It stops when the squared
unbalance over (h + 0.1 mm)² is under 10⁻⁶·(N² + V² + M²/h²) + 1 + (1000·A)², after at
least one step. It fails after 50 steps, when the system cannot be solved, or when a step
is larger than 0.5 in all. With shear it returns found or not found only: the third
status (−2) that the stage control tests for is returned without shear alone.

r2c has it as `Shear.own_solve`, off: what runs is r2c's own solve (Newton's method on the
true residual with a search along the step, then a bracketing search). Measured with it on
(2026-11-22, the eleven shear cases, `tools/changes.py` against the run before): 8 checks
come inside (the post-peak of "constant V, then M", 5.9 to 1.8 %; views at the peak of
M/V = 0.5 m and of the I-girder) and 13 go outside (12 views of V alone at its fall of
load, up to 100 %; transverse bond at the I-girder's peak, 2.5 to 93.5 %), and r2c has
fewer of Response's stages at M/V = 2 m (`tools/stagematch.py`: 59 to 47 of 87). It does
not change what happens on the I-girder at M/V = 1 m. Not used. (Those figures are of the
solve with whole steps throughout; with the step factor, read in step A-1c, they are in
"The shear strain profile between passes".)


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

### The shear strain profile between passes [B], read 2026-11-22 (step A-1c): written, off

What the program does to the shear strain profile within a stage, when it reports a stage
as not solved, and what it carries from one stage to the next (`0041e840`, `0041fe20`,
`004688b0`, `00467f20`, `004b67e0`, `00426f10`, `0041c060`, `004357d0`, `00418af0`,
`004276a0`). The profile is a table over the depth of the shear strain over the section's
shear strain (the third global strain), with a mean of one.

**The update** [`0041e840`], after the calculated shear stress has been found at the top,
middle and bottom of every layer:

* at a node that carries shear: the profile's value times the mean of one and (calculated
  stress over the state's stress); that factor is held within ten either way (a hundred
  for a material named "steel"), and the value within a hundred;
* at a node that carries none (under 10⁻⁸ Pa): the value as it is, plus 10⁻⁶;
* while the section's shear strain is under 10⁻⁸: every value as it is;
* nothing at the top and bottom faces;
* then every value is divided by the profile's mean over the depth, taken by Simpson's
  rule over each layer's three nodes with no width in it (`004b67e0`), the divisor held
  between 0.1 and 10 while there is shear; a mean of exactly nothing puts the profile back
  to that of the uncracked section;
* and no value may be above eight times the gross area over the concrete area within the
  depth that has stiffness (`00426f10`; "The depth that counts", above). The cap is
  applied after the division and the profile is not divided again.

There is no damping in the update. r2c's update (`Shear.update_shape`) differs in four
things: the mean is weighted by the width; a node that carries no shear is given the
calculated stress over its tangent stiffness; a value may not change sign; there is no
cap. On a section of constant width the first makes no difference.

**When the profile update reports a stage as not solved** [`0041fe20`, `004688b0`,
`00467f20`]. The change of the three global strains along the member is solved from the
3 × 3 stiffness by elimination with row pivoting, which gives up when a pivot is under
10⁻⁵ (N and m). Then the fall-backs: axial strain and curvature alone from the first two
equations; else curvature and shear strain from the last two; else the curvature alone
from the moment equation. A fall-back is taken only if what it leaves out of the other
equations is under a thousandth of the shear force; otherwise the update reports the
stage as not solved, and the stage fails. So this happens only where the section has no
stiffness against shear strain at all *and* its bending is coupled to its shear. r2c
does the same in effect (`Shear.shear_flow`: the flexural part alone when there is no
shear stiffness) without the test of a thousandth.

**The passes** [`00418af0`]. In every pass, after the solve and the update: the profile
error and the state code of the state just solved. Then, in this order:

* 16 passes done, the error above 3 % and the load above the largest so far: failed;
* the error above 10 (a thousand per cent) after more than three passes: the profile of
  the uncracked section again (`004357d0`: the first moment of the area beyond a height
  over the width there, brought to a mean of one), and half steps in the solve from then
  on;
* **the state code not zero: failed at once while the step multiplier is 0.5 or more;
  and if the load is under that of the stage before, the stage is taken as it is, in
  this pass**, converged or not;
* state code 3 with the load above the largest so far: failed at once;
* otherwise another pass while the error is 1 % or more and fewer than 16 are done.

r2c tests the state code once, on the stage as the passes leave it. Written as
`Shear.pass_code`, off.

**What a stage leaves behind** [`00418af0`, `0041c060`]. The state of a stage is the one
solved in its last pass, with the profile that pass started from; nothing is evaluated
again when it is accepted. The profile the next stage starts from is the last update's,
whether the stage converged or not. When a stage fails, when a stage is put in between,
and when a stage set aside is taken up again, the profile is rebuilt from a stage's own
node strains (`0041c060`: each node's shear strain over the stage's; the profile of the
uncracked section where the stage's shear strain is under 10⁻⁷). r2c puts back the
profile a stage left behind, which for a converged stage is the update after it, and
after a stage that has not converged it starts the next from the profile that stage was
solved on. Written, with the update, as `Shear.own_profile`, off.

**The step factor of the global solve** [`004276a0`; a correction to "The global solve
with shear", above, which had "whole steps (half steps with the relaxation flag)"].
Every step of that solve is multiplied by a factor the analysis keeps. It is set to one
half once a solve has taken more than ten steps (for a section under 5 m deep), and when
a try at a stage has failed; it is put back to one at the end of every solve, unless the
control variable is the shear strain or the flag is set. The flag is set, and the factor
stays one half for the rest of the response, under control of the axial strain, where
M/V is between 0.15 and 0.75 of the depth (`00419250`), after a change of control
variable (`004162d0`) and after the reset of the profile above. The limit of 50 steps is
100 in the single-state solve. In r2c since step A-1c as part of `Shear.own_solve`
(`step_share`, `half_steps`), which stays off: without it r2c's writing of that solve
ran to its 50 steps at states where the program goes on.

**Measured, each switched on by itself** (2026-11-22, one machine; the 24 cases against
the "before" run of step A-1c with `tools/changes.py` and `tools/targets.py --counts`;
the 16 parked I-girders with shear with `tools/earlyends.py` and `tools/stagematch.py`):

| Switched on | The 24 cases: checks in / out | Cases inside, where it changed | Parked I-girders ending early (3 of 16 before: softening 12, 7, 9) | Response's stages r2c has |
|---|---|---|---|---|
| The tests on every pass | 0 / 7 (all at the peak of M/V = 0.5 m) | Could views 20 to 19 | 3: the same three | as before |
| The profile handling | 11 / 22 | **rising branch 23 to 24** (M/V = 0.5 m, 9.9 to 3.6 %); post-peak 16 to 18; Should views 14 to 16; Could views 20 to 18 | 2: softening 12 and 9 (9 at −5.0 % of the peak against −5.1 %, on the line); softening 7 now reaches +4.8 % | about as before (Newbeam the same; I-girders three up, three down) |
| The program's solve, corrected | 12 / 15 | post-peak 16 to 17; Should views 14 to 16; Could views 20 to 19 | 2: softening 12, and softening 6 instead of 7 and 9 | **fewer**: M/V = 2 m 59 to 47 of 87; three parked I-girders about 41 to 31 |
| Profile handling and solve | 12 / 22 | post-peak 16 to 19; Should views 14 to 15; Could views 20 to 18 | 1: softening 12 | fewer: M/V = 2 m 59 to 53 |

Of the 22 checks that go outside with the profile handling, 11 are one stage of V alone
and are not a difference of state: r2c's fall of load at cracking there is 1.2 % of the
peak (1.9 % before; Response's 2.2 %; the measure counts a fall from 2 %, D32), and the
stage of Response's fall is then compared with r2c's stage before cracking, which has
the same load. Nine are at the peak of M/V = 0.5 m (up to 15.5 %). No Must goes outside
in any of the four.

**What none of them changes:** the views of the column with shear at its flat peak (D47:
eleven views 6 to 28 % off in every run, nine of them of the Must or Should tier); the stage the I-girder at M/V = 1 m keeps and
Response drops (D48); softening 12 at M/V = 2 m, which ends early in every run. On that
case the trace shows what an early end is: after the web cracks both programs have a
stage that has not converged (r2c 144 % off after 16 passes, load 536.0 kN; Response's
stage at the same curvature 533.0 kN) and then a stage whose load is within 0.2 % of
the largest so far: Response's is 0.15 % under it and is kept, r2c's is 0.1 % over it
with 4.3 % of error and is refused. Which side of that line a stage falls on is decided
by a state that has not converged, to a tenth of a per cent.

**A stage refused, or not solved.** The stage is reset to the one before and tried again.
The first time a whole step is refused the target goes half a base step *further* and the
multiplier is marked 1.5, which is the step then being tried; after that the multiplier is
halved each time and the target comes back by the multiplier times the base step, so the
tries are at 1, 1.5, 0.75, 0.375 … of a step [`0041a870`, case 1]. Until 2026-11-22 r2c
went half a step back at the first refusal (a sign read the wrong way), so its tries were
at 1, 0.5, −0.25 … [O: on the I-girder with shear Response's stage after the curvature of
−0.091 rad/km is at −0.031, three quarters of a step on, its peak; r2c now puts its stage
there, 656.2 kN against 655.9, where it had gone back and climbed to 645 in 23 stages]. The
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
| The offset across the member is the shrinkage and thermal profile alone; the second table of the tension zone walk is the outline | above ("What the concrete's offset does") | two cases, both rectangular |
| The first envelope of the Transverse Strain chart | straight between the offsets at the two faces | two cases |
| Interlocking hoops are stirrups | yes | one case (column, M/V = 1 m) |
| Second starting plane and step cut-back for the initial state | above | r2c's own; three cases |

## Not implemented

Out of scope by the owner's decision: hollow sections, long-term effects, strain
discontinuity, the old text input format; and since 2026-11-22 draped tendons (D4) and the
Hsu softening models with Tamai tension stiffening (D5). Beyond the documented scope and
taken out on 2026-11-22 (D10, D18): compression softening 4, 16 and 17, and a segmental
curve for reinforcing steel. r2c refuses these as out of scope; what Response itself rejects
is an input error (`docs/scope.md`, section 3). Response's program folder is not read (D9).
