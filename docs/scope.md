# r2c: scope inventory

Every input an r2x solve can take that reaches the analysis, and where r2c stands on each.
This is the checklist for "scope complete" (the owner's brief for increment S, 2026-11-21).
First written 2026-11-21 by the developer; the statuses are kept up to date as cases are
captured and features built.

## How to read it

**Sources.** What an input file can carry: Response's own schema (`r3g.dtd`, shipped with
Response-2000 1.9.7), the manual (Bentz's thesis, Appendix A, sections 2 and 3 and 5-5 to
5-12), r2x's guide and dialog catalogue (`docs/guide.md`, `docs/dialogs.md`), and r2c's
reader (`src/r2c/inputs.py`, `src/r2c/materials.py`). The solve options are r2x's
(`r2x solve --help`).

**Measured, not assumed.** What Response does with an item was measured with r2x's worker
(r2x 0.5.0, Response-2000 1.9.7 under Wine, 2026-11-21): `tools/variants.py` derives one
input per item from an input already in the test set by stated text edits, and
`tools/probe.py` puts each through Response: its own Save As of the file (how it read it), a
solve, and the same solve of the base (whether the item changes any chart). The numbers are
in `docs/scope-probes.md` (generated); "probe NAME" below names its row. Which fixtures
exercise which feature is from `tools/scope.py` (it reads the fixtures' inputs).

**Status of each item**, one of the owner's four:

| Status | Meaning |
|---|---|
| **compared** | r2c implements it and an oracle case has it (the fixture is named) |
| **not compared** | r2c implements it; no oracle case has it yet (the new case is named) |
| **missing** | r2x solves it; r2c refuses it, or reads it and ignores it (the new case is named) |
| **by design** | out of scope by the owner's decision: hollow sections, long-term effects, strain discontinuity, the old text format |

and two that the measurements made necessary (the developer's addition; reading, for the
owner to confirm):

| Status | Meaning |
|---|---|
| **no effect** | Response accepts it and no chart changes: it does not reach the analysis |
| **not solvable** | r2x cannot solve it: Response rejects the input or fails on it, or r2x's own checks stop the solve. There is nothing to compare with |

"New case" names are the fixtures step 2 of the increment adds. The cases come in two
groups: **A**, those that exercise a kernel path no present case reaches, and **B**,
combinations of paths that are each reached already. The brief asks for A first when there
are more than 15.

---

## 1. The input file (.r2t, .rsp: `<r3g_beam>`)

### 1.1 The file and General settings

| Item | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|
| Several sections in one file (the catalogue) | opens on the first | reads the first | compared | cm4-asis, liping-asis, marshall-*, se100-asis |
| Title, analysis by, date (`name`, `doneby`, `date`) | text only | title read | no effect | |
| Units of the file: SI (`units="metric"`) | | reads | compared | every fixture |
| Units of the file: US (`units="US"`) | reads; solves (probe newbeam-usfile) | reads | not compared | **newbeam-usfile-mv** (A, the brief's), **newbeam-usfile-si-m** (B: `--units si` over a US file) |
| Units of the file: kg-cm (`units="oldmetric"`) | reads; solves (probe newbeam-kgcmfile) | reads | not compared | **newbeam-kgcmfile-mv** (A, the brief's) |
| Units of the file: `roman` (in the schema only) | reads it in a fourth unit system that its Preferences do not offer; r2x records the solve as kg-cm (probe newbeam-roman) | reads it as SI | not solvable (r2x cannot name the units; see open questions) | |
| Crack spacing given (`smx`, `smt`) | solves; peak +3 % on Newbeam, M + V (probe newbeam-smx) | uses them | not compared | **newbeam-smx-mv** (A) |
| Crack spacing automatic | | implemented | compared | every fixture |
| Moment axis given (`axialloc`) | solves; peak +21 % under N = −1000 kN (probe newbeam-axialloc) | uses it | not compared | **newbeam-axialloc-nm** (A) |
| Moment axis at the centroid | | implemented | compared | every fixture with axial load |
| The old text format (Ver_0.8) | | refuses | by design | |

### 1.2 Concrete (`<concrete>`)

| Item | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|
| Strength `fcp`; aggregate size `maxagg`; its reduction above 60 MPa | | implemented | compared | all; 10 mm in cm4-asis; 60 MPa igirder-*, 66 MPa cm4-asis |
| Tensile strength automatic / given (`ft`) | | implemented | compared | all / cm4-asis |
| Strain at peak stress automatic / given (`e0`) | | implemented | compared | all / liping-asis |
| Tension stiffening factor (`tsfactor`) | solves; peak −4 % (probe newbeam-tsfactor) | implemented | not compared | **newbeam-tsfactor-mv** (A) |
| Several concrete types, by region of the outline | | implemented | compared | cm4-asis (two types) |
| Base curve 2, Popovics/Thorenfeldt/Collins (default) | | implemented | compared | all but two |
| Base curve 0, linear | solves (probe newbeam-cmod0) | implemented | not compared | **newbeam-cmod0-m** (A) |
| Base curve 1, parabolic | solves | implemented | compared | se100-asis |
| Base curve 3, elasto-plastic | solves (probe newbeam-cmod3) | implemented | not compared | **newbeam-cmod3-m** (A) |
| Base curve 4, segmental, with its curve | solves | implemented | compared | cm4-asis |
| Compression softening 18, Collins-Bentz 2011 (default) | | implemented | compared | every shear case |
| Compression softening 0, none | solves | implemented | not compared (cm4-asis has it, but without shear nothing softens) | **igirder-csoft0-m2v** (A) |
| Compression softening 2 (Vecchio-Collins 1986), 6 (Mehlhorn et al), 7 (Maekawa et al), 10 (CAN CSA A23.3 M84), 13 (Porasz-Collins 1988) | solves each (probes igirder-csoft2, 6, 7, 10, 13) | has a formula under each number; none has a source in `docs/kernel.md` | not compared | **igirder-csoft2-m2v, -csoft6-, -csoft7-, -csoft10-, -csoft13-** (A) |
| Compression softening 1 (Vecchio-Collins 1982), 3 (Vecchio-Collins 1992-A), 5 (1992-B), 8 (Noguchi et al), 9 (Belarbi-Hsu proportional), 11 (Collins 1978), 12 (Kaufmann-Marti 1998), 14 (Zhang-Hsu 1998 with eta), 15 (Hsu 1993), 16 (Zhu-Hsu-Lee 2001), 17 (Zhang-Hsu 1998, no eta) | solves each on the I-girder (probes igirder-csoft1 … 17; 9 and 11 at M/V = 1 m, since r2x's own check stops them at 2 m). On Newbeam, 1 ends in Response's "No closure on shear distribution" | refuses each | missing | **igirder-csoft1-m2v, -csoft3-, -csoft5-, -csoft8-, -csoft12-, -csoft14-, -csoft15-, -csoft16-, -csoft17-m2v; igirder-csoft9-mv, -csoft11-mv** (A) |
| Compression softening 4 (no name in the dialogs; printed as "Unsupported Method") | solves, with a result of its own (probe igirder-csoft4) | refuses | missing | **igirder-csoft4-m2v** (A) |
| Tension stiffening 7, Bentz 1999 (default) | | implemented | compared | all |
| Tension stiffening 1 (Vecchio-Collins 1982), 2 (Collins-Mitchell 1987), 3 (Izumo et al), 4 (Tamai et al), 6 (elasto-plastic) | solves each; peaks −4 to +9 % (probes newbeam-tstiff1 … 6) | implemented | not compared | **newbeam-tstiff1-mv, -tstiff2-, -tstiff3-, -tstiff4-, -tstiff6-mv** (A) |
| Tension stiffening 0, none | Response asks "Do you wish to leave tension off?" before solving; r2x stops at the question (probe newbeam-tstiff0) | implemented | not solvable | |
| Tension stiffening 5 (Stuart Oliver) | Response refuses the file: "Stuart Oliver Model Unsupported" (probe newbeam-tstiff5) | reads it as the default | not solvable | |

The softening cases are on the I-girder with strands at M/V = 2 m because that is where the
web's compression decides the response: on Newbeam at M/V = 1 m the softening models move the
peak by less than 0.3 % (probes newbeam-csoft0 … 17), on the I-girder by −9 to +6 %.

### 1.3 Steel types (`<rebar>`, `<prestress>`)

| Item | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|
| Reinforcing steel: fy, E, fu, εsh, εu | | implemented | compared | all |
| Reinforcing steel with a segmental curve | reads the curve, rewrites fy and εsh from it, solves; peak +6 % (probe newbeam-segsteel) | reads the curve and ignores it | missing | **newbeam-segsteel-m** (A) |
| Prestressing steel: fu, E, εu, Ramberg-Osgood A, B, C | | implemented | compared | igirder-* (defaults), cm4-asis (A, B, C given) |
| Prestressing steel with a segmental curve | drops the curve on reading; no chart changes (probe igirder-segstrand) | does not read it | no effect | |
| Predefined steel types | they are sets of the numbers above | | compared | |

### 1.4 The concrete outline (`<sectionSOLID>`, `<shapesection>`)

| Item | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|
| Rows of elevation and width; a step in width; a tapering width; a concrete type per region | | implemented | compared | rectangle: Newbeam and others; step: tbeam-*, igirder-*, cm4-asis; taper: column-*, liping-asis, cm4-asis |
| A circle, as Response writes one: 13 straight rows | analyses the polygon | implemented | compared | column-* |
| Elevations below zero | shifts the section to start at zero; same charts but one rounding (probe newbeam-negelev) | implemented | not compared | **newbeam-negelev-m** (B) |
| Curved rows: a lone `UP` or `DOWN` line, or a width of `UP` or `DOWN` | rejects the file: "Error in Quotes!" (probes column-curved, column-curvedwidth). Curves exist in shape.dat and in the outline dialog only; Response turns them into straight rows there, and writes the rows | reads a lone line and ignores it; refuses a width | not solvable (see below) | |
| A shape without an outline (`<shapesection>` alone: RECT, CIRCLE, TBEAM, IBEAM) | opens the file with an empty outline; the solve fails: "bad request" (probes newbeam-, tbeam-, column-nooutline) | builds the outline from the shape's dimensions | not solvable (see below) | |
| A shape beside an outline | the outline is the section; the shape is a label | reads the outline | compared | all |
| Hollow sections (`<sectionHOLLOW>`) | | refuses | by design | |

### 1.5 Longitudinal reinforcement and tendons (`<longreinfx>`)

| Item | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|
| Layers of bars by title or by area; number, area, elevation | | implemented | compared | all; by area: cm4-asis, liping-asis |
| Tendons with a prestrain (`dep`) | | implemented | compared | igirder-*, cm4-asis |
| A prestrain on bars that are not prestressing steel | solves; peak +0.6 % (probe newbeam-bardep) | implemented (the tendons' path) | not compared | **newbeam-bardep-m** (B) |
| Draped tendons (`drape`) | solves; every chart changes, the peak by less than 0.1 % (probe igirder-drape) | reads it and ignores it | missing | **igirder-drape-m2v** (A) |
| Circular pattern (`pattern="1"`, `nround`, `aligned`, `index`) | the layers are in the file one by one | reads the layers | compared | column-* |
| Distributed pattern (`pattern="2"`, `index`) | no chart changes (probe newbeam-longpattern2) | reads the layers | no effect | |
| Bar spacing in a layer (`space`) | no chart changes (probe newbeam-barspace) | reads it, does not use it | no effect | (liping-asis has it) |

### 1.6 Transverse reinforcement (`<transreinfz>`)

| Item | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|
| Area, spacing, top and bottom, by title or by area; several sets | | implemented | compared | all shear cases; cm4-asis, liping-asis |
| None, with shear | solves; peak −38 % (probe newbeam-nostirrups) | implemented | not compared | **newbeam-nostirrups-mv** (A) |
| Pattern 1 single leg, 2 open, 3 closed, 5 T-headed single leg | on Newbeam every chart is the same byte for byte whichever of these (and 6) the stirrup is given as (probes newbeam-pattern1, 2, 3, 6) | the area is the file's | compared | 1: liping-asis; 2: dmn1n-asis, igirder-*; 3: marshall-*, se100-asis, tbeam-*, cm4-asis; 5: every Newbeam case |
| Pattern 4, hoop | | implemented | compared | column-* |
| Pattern 6, interlocking hoops | on the circular column not what a hoop gives: peak +1.4 % (probe column-interlock) | treats it as stirrups with two legs | not compared | **column-interlock-mv** (A, the brief's) |
| Pattern 7, horizontal tie | as a stirrup, but with no transverse bond (one chart differs, probe newbeam-pattern7) | treats it as a stirrup | compared | liping-asis (the ties there have no depth) |
| Prestrain on stirrups (`dep`) | solves; peak +0.9 % (probe newbeam-stirrupdep) | implemented | not compared | **newbeam-stirrupdep-mv** (A) |

T-headed stirrups, in the brief's list of new cases, are compared already: Newbeam's own
stirrup is the T-headed single leg (pattern 5; Response's Quick Define default), in all 18
Newbeam fixtures (reading, for the owner to confirm).

### 1.7 Loads, strains and analysis options in the file

| Item | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|
| Loads (`<sectloading>`) | used when no option overrides them (probe newbeam-loads) | implemented | compared | the as-is cases take their loads from the files (cm4-, dmn1n-, liping-, marshall-, se100-asis); verify passes them as options, as r2x records them |
| Shrinkage and thermal strain of the concrete over the depth (`<shrinktherm>`) | solves; every chart changes (probes newbeam-shrink, newbeam-thermgrad) | reads it and ignores it | missing | **newbeam-shrink-m, newbeam-thermgrad-m** (A) |
| Thermal strain of a bar layer (`<rebarthermx>`) | solves; peak −0.3 % (probe newbeam-bartherm) | implemented (taken off the prestrain) | not compared | **newbeam-bartherm-m** (A) |
| Material factors in the file (`<analysisoptions phic, phis, phip>`) | used (probe newbeam-csafile) | implemented | not compared | **newbeam-csafile-m**, **newbeam-csafile-none-m** (`--factors none` over them) (B) |
| Strain discontinuity (`<straindiscont>`) | | refuses | by design | |
| Long-term effects (`<analysisoptions longterm, sustainM, sustainN, age>`) | | refuses | by design | |
| `<analysisoptions clamp>` | dropped on saving; no chart changes (probe newbeam-clamp) | does not read it | no effect | |
| `<firedata>` | no chart changes (probe newbeam-fire) | does not read it | no effect | |
| Member data (`<eleminfo>`, `<R2010_Analysis>`) | for the member response, which r2x does not run | does not read it | no effect | |

### 1.8 Response's program folder

| Item | What r2x does | r2c | Status |
|---|---|---|---|
| `rebar.dat`, the bar list | passes the linked folder's file to Response | has the shipped list built in (all 125 bars the same, checked against the shipped file 2026-11-21) | compared for the shipped list; an edited list is not read (see open questions) |
| `shape.dat`, the shapes of Quick Define | used when a section is defined, not when one is solved | | no effect on a solve |
| `r2k.r2k`, the template for File > New | a solve without an input starts from it if the folder has one | always starts from Newbeam | compared without a template (newbeam-new); with one: see open questions |

---

## 2. Solve options

| Option | r2c | Status | Case |
|---|---|---|---|
| `--units si` | implemented | compared | most fixtures |
| `--units us` over an SI file | implemented | compared | newbeam-us, newbeam-us-mv |
| `--units kgcm` over an SI file | implemented | compared without shear (newbeam-kgcm); with shear through the kg-cm file | **newbeam-kgcmfile-mv** (A) |
| `--units si` over a file in other units | implemented | not compared | **newbeam-usfile-si-m** (B) |
| `--factors none` | implemented | compared | most fixtures |
| `--factors csa`, without shear | implemented | compared | newbeam-csa |
| `--factors csa`, with shear | implemented | not compared | **newbeam-csa-mv** (A, the brief's) |
| `--initial`, `--increment`: moment alone, either sign | implemented | compared | newbeam-m, newbeam-negm, tbeam-*, cm4-asis and others |
| … axial load alone, either sign | implemented | compared | newbeam-nonly, column-nonly, marshall-nonly; newbeam-tension |
| … constant compression, moment increasing | implemented | compared | newbeam-n2000-m, column-n4000-m |
| … axial load and moment increasing together | implemented | compared | newbeam-nm |
| … moment and shear increasing, either sign of moment | implemented | compared | ten cases; marshall-asis (M −) |
| … shear alone | implemented | compared | newbeam-vonly |
| … constant compression, moment and shear increasing | implemented | compared | newbeam-nmv, liping-asis |
| … `0,0,0`: the initial load alone | implemented | compared | newbeam-zero |
| … constant tension, moment increasing | implemented | not compared | **newbeam-ntension-m** (B) |
| … constant compression, shear increasing alone | implemented | not compared | **newbeam-ncomp-v** (B) |
| … constant shear, moment increasing | implemented | not compared | **newbeam-v0-m** (B) |
| … a constant moment, moment and shear increasing | implemented | not compared | **newbeam-m0neg-mv** (B) |
| … axial load, moment and shear increasing together | implemented | not compared | **newbeam-nmv-incr** (B) |
| … constant tension with moment and shear; a constant moment with shear alone; axial load and shear together | implemented | not solvable on Newbeam: r2x's own check stops the first two ("Response has more than the N stages on its control curves"), Response fails on the third ("No closure on shear distribution") (probes newbeam-loads-ntension-mv, -m0-v, -nv) | |
| … a negative shear | refuses, as Response's dialog does | (Response's own rule: the manual, 3-5) | |
| `--more-detail N`, without shear | implemented | compared | newbeam-m-md2 |
| `--more-detail N`, with shear | implemented | not compared | **newbeam-mv-md2** (A, the brief's) |
| `--more-detail max` | implemented | not compared | **newbeam-m-mdmax** (B) |
| `--stage`, `--views` | implemented | compared: they choose what is written, not what is solved; every fixture is cut from a capture of every stage and all four views | all |
| No input (File > New) | implemented | compared | newbeam-new |

Other sections under shear, from the brief's list:

| Item | Status | Case |
|---|---|---|
| T-beam with moment and shear | not compared | **tbeam-m2v** (A, the brief's) |
| I-girder at M/V = 1 m (the base of igirder-csoft9-mv and -csoft11-mv) | not compared | **igirder-mv** (B) |

---

## 3. What "scope complete" needs

Judged against this inventory, the scope is complete when

1. every **missing** item is built, with its rule and source in `docs/kernel.md`: eleven
   named compression softening models and number 4, the segmental steel curve, draped
   tendons, shrinkage and thermal strains of the concrete;
2. every **missing** and **not compared** item has its case in `tests/oracle` and is
   reported in `docs/verification-results.md`;
3. r2c refuses only what is **by design**, and treats as input errors the files Response
   itself rejects (see below).

The count of new cases: 41 in group A, 12 in group B.

### Items Response or r2x does not solve

These were on the brief's list of refusals to build ("curved and elliptical outline rows",
"shapes given without an explicit outline") or follow from it, and the measurement says
r2x does not solve them. Nothing is built for them and no case can be captured; what r2c
does with each is the developer's proposal, for the owner to confirm.

- **Curved outline rows in an input file.** Response's XML reader rejects both forms. In
  the binary the words UP and DOWN are used by the reader of shape.dat (`004f96e0`) and by
  the width field of the outline dialog (`00448d90`) only; a circle defined in Response is
  saved as 13 straight rows (r2x's `quick-column/hand.r2t`). So a curved row never reaches
  the analysis: option C4 of `docs/status.md` falls away. r2c reads a lone UP or DOWN line
  and ignores it, which analyses a different section without saying so. Proposal: r2c
  rejects both forms as an input error, as Response does.
- **A shape without an outline.** Response opens the file with no concrete and the solve
  fails. r2c builds the outline from the shape's dimensions. Proposal: leave it, as a
  convenience that is not compared; or reject it as Response does. The owner's choice.
- **Tension stiffening "None"** needs an answer to Response's question that r2x does not
  give. r2c implements it (the thesis' base case). It stays not compared until r2x answers
  the question.
- **Tension stiffening 5**: Response refuses the file. r2c reads it as the default.
  Proposal: r2c rejects it as an input error, as Response does.
- **`units="roman"`**: see the table. Proposal: r2c rejects it as an input error.
- **Three load combinations on Newbeam** (table in section 2): they may solve on another
  section; not pursued.

### Open questions for the owner

1. The two added statuses, **no effect** and **not solvable**, and the proposals above.
2. Response's program folder: is an edited `rebar.dat`, or a template `r2k.r2k`, an input
   r2c should read? r2x passes the folder to Response; r2c has no notion of a program
   folder. Not built in this increment.
3. Compression softening 4 has no name in Response's dialogs and prints as "Unsupported
   Method", but a file can carry it and Response solves it. It is in the inventory as
   missing; say if it should be by design instead.
4. T-headed stirrups are counted as compared already (section 1.6).
