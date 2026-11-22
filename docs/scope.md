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

**Documented.** Each item is marked as documented or not (2026-11-22), by the owner's rule
(D17 in `docs/summary.md`): the manual, Appendix A of Bentz's thesis, says which features
exist; the thesis says how they calculate. "A-16" is the manual's page; "no" means the manual
does not have the item. Where an item is named in the manual and its rule is in neither
document, the column says so. Completion is judged against the documented items (owner,
2026-11-22); what r2c had built beyond them is removed (D18).

**Status of each item**, one of the owner's four:

| Status | Meaning |
|---|---|
| **compared** | r2c implements it and an oracle case has it (the fixture is named) |
| **not compared** | r2c implements it; no oracle case has it |
| **missing** | r2x solves it; r2c refuses it, or reads it and ignores it (its oracle case is named) |
| **by design** | out of scope by the owner's decision: hollow sections, long-term effects, strain discontinuity, the old text format |

two that the measurements made necessary (the developer's addition; confirmed by the owner,
2026-11-22, D8):

| Status | Meaning |
|---|---|
| **no effect** | Response accepts it and no chart changes: it does not reach the analysis |
| **not solvable** | r2x cannot solve it: Response rejects the input or fails on it, or r2x's own checks stop the solve. There is nothing to compare with |

and one that follows from the owner's decisions of 2026-11-22 (D4, D5, D10, D18):

| Status | Meaning |
|---|---|
| **removed** | beyond the documented scope, or out of scope by a decision: r2c had it and it was taken out on 2026-11-22. r2c refuses the input as out of scope (exit status 3), although Response solves it. Its fixture, if it has one, is parked |

Case names in bold are the 53 fixtures step 2 of increment S added (2026-11-21; listed by
`tools/scope_cases.py --list`). They come in two groups: **A**, those that exercise a kernel
path no earlier case reaches, and **B**, combinations of paths that are each reached already.
"Compared" says that an oracle case has the item and r2c can be run against it; whether r2c
is inside target on the case is in `docs/verification-results.md` when its set was run. Since
2026-11-22 only the 17 load cases on Newbeam are run by default (the phase A set, in
`tests/oracle`); every other case named here is parked in `tests/oracle/parked`.

---

## 1. The input file (.r2t, .rsp: `<r3g_beam>`)

### 1.1 The file and General settings

| Item | Documented | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|---|
| Several sections in one file (the catalogue) | no: Response-2000 takes one cross section per file (A-7, A-28) | opens on the first | refuses (since 2026-11-22, D23; before, it read the first) | removed | cm4-asis, liping-asis, marshall-*, se100-asis: refused, fixtures kept |
| Title, analysis by, date (`name`, `doneby`, `date`) | yes: A-11 | text only | title read | no effect | |
| Units of the file: SI (`units="metric"`) | yes: A-7, A-80 | | reads | compared | every fixture |
| Units of the file: US (`units="US"`) | yes: A-7, A-80 | reads; solves (probe newbeam-usfile) | reads | compared since 2026-11-21 | **newbeam-usfile-mv** (A, the brief's), **newbeam-usfile-si-m** (B: `--units si` over a US file) |
| Units of the file: kg-cm (`units="oldmetric"`) | yes: A-7, A-80 | reads; solves (probe newbeam-kgcmfile) | reads | compared since 2026-11-21 | **newbeam-kgcmfile-mv** (A, the brief's) |
| Units of the file: `roman` (in the schema only) | no | reads it in a fourth unit system that its Preferences do not offer; r2x records the solve as kg-cm (probe newbeam-roman) | rejects the file as an input error (since 2026-11-21; before, it read it as SI) | not solvable (r2x cannot name the units; see open questions) | |
| Crack spacing given (`smx`, `smt`) | yes: A-11 | solves; peak +3 % on Newbeam, M + V (probe newbeam-smx) | uses them | compared since 2026-11-21 | **newbeam-smx-mv** (A) |
| Crack spacing automatic | yes: A-11 | | implemented | compared | every fixture |
| Moment axis given (`axialloc`) | yes: A-12 | solves; peak +21 % under N = −1000 kN (probe newbeam-axialloc) | uses it | compared since 2026-11-21 | **newbeam-axialloc-nm** (A) |
| Moment axis at the centroid | yes: A-12 | | implemented | compared | every fixture with axial load |
| The old text format (Ver_0.8) | yes: A-80 to A-83 | | refuses | by design | |

### 1.2 Concrete (`<concrete>`)

| Item | Documented | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|---|
| Strength `fcp`; aggregate size `maxagg`; its reduction above 60 MPa | yes: A-15 | | implemented | compared | all; 10 mm in cm4-asis; 60 MPa igirder-*, 66 MPa cm4-asis |
| Tensile strength automatic / given (`ft`) | yes: A-14, A-15 | | implemented | compared | all / cm4-asis |
| Strain at peak stress automatic / given (`e0`) | yes: A-14, A-15 | | implemented | compared | all / liping-asis |
| Tension stiffening factor (`tsfactor`) | yes: A-15 | solves; peak −4 % (probe newbeam-tsfactor) | implemented | compared since 2026-11-21 | **newbeam-tsfactor-mv** (A) |
| Several concrete types, by region of the outline | yes: A-13, A-14 | | implemented | compared | cm4-asis (two types) |
| Base curve 2, Popovics/Thorenfeldt/Collins (default) | yes: A-15; thesis p. 57 | | implemented | compared | all but two |
| Base curve 0, linear | yes: A-15 | solves (probe newbeam-cmod0) | implemented | compared since 2026-11-21 | **newbeam-cmod0-m** (A) |
| Base curve 1, parabolic | yes: A-15; thesis p. 57 | solves | implemented | compared | se100-asis |
| Base curve 3, elasto-plastic | yes: A-15 | solves (probe newbeam-cmod3) | implemented | compared since 2026-11-21 | **newbeam-cmod3-m** (A) |
| Base curve 4, segmental, with its curve | yes: A-15, A-72 | solves | implemented | compared | cm4-asis |
| Compression softening 18, Collins-Bentz 2011 (default) | no: later than the manual. Up to 56.7 MPa it is the thesis' own equation (p. 58 to 59); see D22 | | implemented | compared | every shear case |
| Compression softening 0, none | yes: A-16 | solves | implemented | compared since 2026-11-21 (cm4-asis has it too, but without shear nothing softens) | **igirder-csoft0-m2v** (A) |
| Compression softening 2 (Vecchio-Collins 1986), 6 (Mehlhorn et al), 7 (Maekawa et al), 10 (CAN CSA A23.3 M84), 13 (Porasz-Collins 1988) | named: A-16 (10 as "CAN CSA S474"). Rule in the thesis for 2 and 13 (p. 58 to 59, in ε1 alone); the others' rules are the binary's; see D21 | solves each (probes igirder-csoft2, 6, 7, 10, 13) | implemented; the formulas r2c had are the binary's (checked 2026-11-21) | compared since 2026-11-21 | **igirder-csoft2-m2v, -csoft6-, -csoft7-, -csoft10-, -csoft13-** (A) |
| Compression softening 1 (Vecchio-Collins 1982), 3 (Vecchio-Collins 1992-A), 5 (1992-B), 8 (Noguchi et al), 9 (Belarbi-Hsu proportional), 11 (Collins 1978), 12 (Kaufmann-Marti 1998), 14 (Hsu-Zhang 1998; "Zhang-Hsu 1998 with eta" in the program), 15 (Hsu 1993) | named: A-16; their rules are the binary's; see D21 | solves each on the I-girder (probes igirder-csoft1 … 15; 9 and 11 at M/V = 1 m, since r2x's own check stops them at 2 m). On Newbeam, 1 ends in Response's "No closure on shear distribution" | implemented since 2026-11-21 (`docs/kernel.md`, "Compression softening"); kept until D21 is answered | compared since 2026-11-21 (parked) | **igirder-csoft1-m2v, -csoft3-, -csoft5-, -csoft8-, -csoft12-, -csoft14-, -csoft15-m2v; igirder-csoft9-mv, -csoft11-mv** (A) |
| Compression softening 16 (Zhu-Hsu-Lee 2001), 17 (Zhang-Hsu 1998, no eta) | no: both are later than the manual | solves each (probes igirder-csoft16, 17) | refuses the file as out of scope (built 2026-11-21, taken out 2026-11-22: D18) | **removed** | **igirder-csoft16-m2v, -csoft17-m2v** (parked; r2c refuses their inputs) |
| Compression softening 4 (no name in the dialogs; printed as "Unsupported Method") | no | solves, with a result of its own (probe igirder-csoft4) | refuses the file as out of scope (built 2026-11-21, taken out 2026-11-22: D10) | **removed** | **igirder-csoft4-m2v** (parked; r2c refuses its input) |
| A Hsu softening model (9, 14, 15) with Tamai tension stiffening (4): Response's "RA-STM mode" | yes: A-16. Out of scope by the owner's decision (D5) | runs with a steel ratio and a tensile strength of its own (the binary; not probed) | refuses the file as out of scope (never built; before 2026-11-22 it ran the two models as if they were independent) | **removed** | |
| Tension stiffening 7, Bentz 1999 (default) | yes: A-16 ("Bentz 2000"); thesis 5-3, 5-4 | | implemented | compared | all |
| Tension stiffening 1 (Vecchio-Collins 1982), 2 (Collins-Mitchell 1987), 3 (Izumo et al), 4 (Tamai et al), 6 (elasto-plastic) | yes: A-16 | solves each; peaks −4 to +9 % (probes newbeam-tstiff1 … 6) | implemented | compared since 2026-11-21 | **newbeam-tstiff1-mv, -tstiff2-, -tstiff3-, -tstiff4-, -tstiff6-mv** (A) |
| Tension stiffening 0, none | yes: A-16 | Response asks "Do you wish to leave tension off?" before solving; r2x stops at the question (probe newbeam-tstiff0) | implemented | not solvable | |
| Tension stiffening 5 (Stuart Oliver) | no | Response refuses the file: "Stuart Oliver Model Unsupported" (probe newbeam-tstiff5) | rejects the file as an input error (since 2026-11-21) | not solvable | |

The softening cases are on the I-girder with strands at M/V = 2 m because that is where the
web's compression decides the response: on Newbeam at M/V = 1 m the softening models move the
peak by less than 0.3 % (probes newbeam-csoft0 … 17), on the I-girder by −9 to +6 %.

### 1.3 Steel types (`<rebar>`, `<prestress>`)

| Item | Documented | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|---|
| Reinforcing steel: fy, E, fu, εsh, εu | yes: A-17 | | implemented | compared | all |
| Reinforcing steel with a segmental curve | no: the manual's curve is "linear to yield, flat post yield, and quadratic after strain hardening" (A-17) | reads the curve, rewrites fy and εsh from it, solves; peak +6 % (probe newbeam-segsteel) | refuses the file as out of scope (built 2026-11-21, taken out 2026-11-22: D18) | **removed** | **newbeam-segsteel-m** (parked; r2c refuses its input) |
| Prestressing steel: fu, E, εu, Ramberg-Osgood A, B, C | yes: A-18 | | implemented | compared | igirder-* (defaults), cm4-asis (A, B, C given) |
| Prestressing steel with a segmental curve | no | drops the curve on reading; no chart changes (probe igirder-segstrand) | does not read it | no effect | |
| Predefined steel types | yes: A-17, A-18 | they are sets of the numbers above | | compared | |

### 1.4 The concrete outline (`<sectionSOLID>`, `<shapesection>`)

| Item | Documented | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|---|
| Rows of elevation and width; a step in width; a tapering width; a concrete type per region | yes: A-20 | | implemented | compared | rectangle: Newbeam and others; step: tbeam-*, igirder-*, cm4-asis; taper: column-*, liping-asis, cm4-asis |
| A circle, as Response writes one: 13 straight rows | yes: A-20 (rows); A-21 for how a circle is entered | analyses the polygon | implemented | compared | column-* |
| Elevations below zero | yes: A-20 | shifts the section to start at zero; same charts but one rounding (probe newbeam-negelev) | implemented | compared since 2026-11-21 | **newbeam-negelev-m** (B) |
| Curved rows: a lone `UP` or `DOWN` line, or a width of `UP` or `DOWN` | yes, in the outline dialog and shape.dat: A-20, A-21, A-77; not in an input file | rejects the file: "Error in Quotes!" (probes column-curved, column-curvedwidth). Curves exist in shape.dat and in the outline dialog only; Response turns them into straight rows there, and writes the rows | rejects the file as an input error (since 2026-11-21; before, it read a lone line and ignored it) | not solvable (see below) | |
| A shape without an outline (`<shapesection>` alone: RECT, CIRCLE, TBEAM, IBEAM) | no | opens the file with an empty outline; the solve fails: "bad request" (probes newbeam-, tbeam-, column-nooutline) | rejects the file as an input error, as Response in effect does (since 2026-11-22: D6; before, it built the outline from the shape's dimensions) | not solvable | |
| A shape beside an outline | yes: A-19, A-20 | the outline is the section; the shape is a label | reads the outline | compared | all |
| Hollow sections (`<sectionHOLLOW>`) | yes: A-9; "unsupported for now" in the text format (A-81) | | refuses | by design | |

### 1.5 Longitudinal reinforcement and tendons (`<longreinfx>`)

| Item | Documented | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|---|
| Layers of bars by title or by area; number, area, elevation | yes: A-22 | | implemented | compared | all; by area: cm4-asis, liping-asis |
| Tendons with a prestrain (`dep`) | yes: A-26 | | implemented | compared | igirder-*, cm4-asis |
| A prestrain on bars that are not prestressing steel | yes: A-81 (a prestrain on any layer), A-35 | solves; peak +0.6 % (probe newbeam-bardep) | implemented (the tendons' path) | compared since 2026-11-21 | **newbeam-bardep-m** (B) |
| Draped tendons (`drape`) | yes: A-26. Out of scope by the owner's decision (D4) | solves; every chart changes, the peak by less than 0.1 % (probe igirder-drape) | refuses a file with a drape other than zero as out of scope (since 2026-11-22: D4; before, it read the drape and ignored it) | **removed** | **igirder-drape-m2v** (parked; r2c refuses its input) |
| Circular pattern (`pattern="1"`, `nround`, `aligned`, `index`) | yes: A-25 | the layers are in the file one by one | reads the layers | compared | column-* |
| Distributed pattern (`pattern="2"`, `index`) | yes: A-25 | no chart changes (probe newbeam-longpattern2) | reads the layers | no effect | |
| Bar spacing in a layer (`space`) | no (Response-2000 asks for the number of bars: A-22) | no chart changes (probe newbeam-barspace) | reads it, does not use it | no effect | (liping-asis has it) |

### 1.6 Transverse reinforcement (`<transreinfz>`)

| Item | Documented | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|---|
| Area, spacing, top and bottom, by title or by area; several sets | yes: A-27 | | implemented | compared | all shear cases; cm4-asis, liping-asis |
| None, with shear | yes (a section without any) | solves; peak −38 % (probe newbeam-nostirrups) | implemented | compared since 2026-11-21 | **newbeam-nostirrups-mv** (A) |
| Pattern 1 single leg, 2 open, 3 closed, 5 T-headed single leg | yes: A-27 | on Newbeam every chart is the same byte for byte whichever of these (and 6) the stirrup is given as (probes newbeam-pattern1, 2, 3, 6) | the area is the file's | compared | 1: liping-asis; 2: dmn1n-asis, igirder-*; 3: marshall-*, se100-asis, tbeam-*, cm4-asis; 5: every Newbeam case |
| Pattern 4, hoop | yes: A-27; thesis 7-6 | | implemented | compared | column-* |
| Pattern 6, interlocking hoops | yes, in Quick Define: A-10 (D11) | on the circular column not what a hoop gives: peak +1.4 % (probe column-interlock) | treats it as stirrups (within 0.8 % in shear in Response's peak state) | compared since 2026-11-21 | **column-interlock-mv** (A, the brief's) |
| Pattern 7, horizontal tie | no | as a stirrup, but with no transverse bond (one chart differs, probe newbeam-pattern7) | refuses (since 2026-11-22, D23; before, it treated it as a stirrup) | removed | liping-asis (the ties there have no depth): refused, fixture kept |
| Prestrain on stirrups (`dep`) | yes: A-82 | solves; peak +0.9 % (probe newbeam-stirrupdep) | implemented | compared since 2026-11-21 | **newbeam-stirrupdep-mv** (A) |

T-headed stirrups, in the brief's list of new cases, are compared already: Newbeam's own
stirrup is the T-headed single leg (pattern 5; Response's Quick Define default), in all 18
Newbeam fixtures (reading, for the owner to confirm).

### 1.7 Loads, strains and analysis options in the file

| Item | Documented | What Response does (measured) | r2c | Status | Case |
|---|---|---|---|---|---|
| Loads (`<sectloading>`) | yes: A-33 | used when no option overrides them (probe newbeam-loads) | implemented | compared | the as-is cases take their loads from the files (cm4-, dmn1n-, liping-, marshall-, se100-asis); verify passes them as options, as r2x records them |
| Shrinkage and thermal strain of the concrete over the depth (`<shrinktherm>`) | yes: A-34 | solves; every chart changes (probes newbeam-shrink, newbeam-thermgrad) | implemented since 2026-11-21 (`docs/kernel.md`, Geometry and strain state) | compared since 2026-11-21 | **newbeam-shrink-m, newbeam-thermgrad-m** (A) |
| Thermal strain of a bar layer (`<rebarthermx>`) | yes: A-34, A-35 | solves; peak −0.3 % (probe newbeam-bartherm) | implemented (taken off the prestrain) | compared since 2026-11-21 | **newbeam-bartherm-m** (A) |
| Material factors in the file (`<analysisoptions phic, phis, phip>`) | yes: A-72 | used (probe newbeam-csafile) | implemented | compared since 2026-11-21 | **newbeam-csafile-m**, **newbeam-csafile-none-m** (`--factors none` over them) (B) |
| Strain discontinuity (`<straindiscont>`) | yes: A-36, A-73 | | refuses | by design | |
| Long-term effects (`<analysisoptions longterm, sustainM, sustainN, age>`) | yes: A-33, A-34 | | refuses | by design | |
| `<analysisoptions clamp>` | no | dropped on saving; no chart changes (probe newbeam-clamp) | does not read it | no effect | |
| `<firedata>` | no | no chart changes (probe newbeam-fire) | does not read it | no effect | |
| Member data (`<eleminfo>`, `<R2010_Analysis>`) | yes: A-36, A-37 | for the member response, which r2x does not run | does not read it | no effect | |

### 1.8 Response's program folder

| Item | Documented | What r2x does | r2c | Status |
|---|---|---|---|---|
| `rebar.dat`, the bar list | yes: A-76 | passes the linked folder's file to Response | has the shipped list built in (all 125 bars the same, checked against the shipped file 2026-11-21) | compared for the shipped list; an edited list is not read (owner, 2026-11-22: D9) |
| `shape.dat`, the shapes of Quick Define | yes: A-77 | used when a section is defined, not when one is solved | | no effect on a solve |
| `r2k.r2k`, the template for File > New | yes: A-79 | a solve without an input starts from it if the folder has one | always starts from Newbeam | compared without a template (newbeam-new); a template is not read (owner, 2026-11-22: D9) |

---

## 2. Solve options

| Option | Documented | r2c | Status | Case |
|---|---|---|---|---|
| `--units si` | yes: A-7 | implemented | compared | most fixtures |
| `--units us` over an SI file | yes: A-7 | implemented | compared | newbeam-us, newbeam-us-mv |
| `--units kgcm` over an SI file | yes: A-7 | implemented | compared without shear (newbeam-kgcm); with shear through the kg-cm file | **newbeam-kgcmfile-mv** (A) |
| `--units si` over a file in other units | yes: A-7 | implemented | compared since 2026-11-21 | **newbeam-usfile-si-m** (B) |
| `--factors none` | yes: A-72 | implemented | compared | most fixtures |
| `--factors csa`, without shear | yes: A-72 | implemented | compared | newbeam-csa |
| `--factors csa`, with shear | yes: A-72 | implemented | compared since 2026-11-21 | **newbeam-csa-mv** (A, the brief's) |
| `--initial`, `--increment`: moment alone, either sign | yes: A-33, A-40 | implemented | compared | newbeam-m, newbeam-negm, tbeam-*, cm4-asis and others |
| … axial load alone, either sign | yes: A-33, A-40 | implemented | compared | newbeam-nonly, column-nonly, marshall-nonly; newbeam-tension |
| … constant compression, moment increasing | yes: A-33, A-40 | implemented | compared | newbeam-n2000-m, column-n4000-m |
| … axial load and moment increasing together | yes: A-33, A-40 | implemented | compared | newbeam-nm |
| … moment and shear increasing, either sign of moment | yes: A-33, A-40 | implemented | compared | ten cases; marshall-asis (M −) |
| … shear alone | yes: A-33, A-40 | implemented | compared | newbeam-vonly |
| … constant compression, moment and shear increasing | yes: A-33, A-40 | implemented | compared | newbeam-nmv, liping-asis |
| … `0,0,0`: the initial load alone | yes: A-33, A-40 | implemented | compared | newbeam-zero |
| … constant tension, moment increasing | yes: A-33, A-40 | implemented | compared since 2026-11-21 | **newbeam-ntension-m** (B) |
| … constant compression, shear increasing alone | yes: A-33, A-40 | implemented | compared since 2026-11-21 | **newbeam-ncomp-v** (B) |
| … constant shear, moment increasing | yes: A-33, A-40 | implemented | compared since 2026-11-21 | **newbeam-v0-m** (B) |
| … a constant moment, moment and shear increasing | yes: A-33, A-40 | implemented | compared since 2026-11-21 | **newbeam-m0neg-mv** (B) |
| … axial load, moment and shear increasing together | yes: A-33, A-40 | implemented | compared since 2026-11-21 | **newbeam-nmv-incr** (B) |
| … constant tension with moment and shear; a constant moment with shear alone; axial load and shear together | yes: A-33, A-40 | implemented | not solvable on Newbeam: r2x's own check stops the first two ("Response has more than the N stages on its control curves"), Response fails on the third ("No closure on shear distribution") (probes newbeam-loads-ntension-mv, -m0-v, -nv) | |
| … a negative shear | yes: A-33 | refuses, as Response's dialog does | (Response's own rule: the manual, 3-5) | |
| `--more-detail N`, without shear | yes: A-40 | implemented | compared | newbeam-m-md2 |
| `--more-detail N`, with shear | yes: A-40 | implemented | compared since 2026-11-21 | **newbeam-mv-md2** (A, the brief's) |
| `--more-detail max` | yes: A-40 | implemented | compared since 2026-11-21 | **newbeam-m-mdmax** (B) |
| `--stage`, `--views` | r2x's own | implemented | compared: they choose what is written, not what is solved; every fixture is cut from a capture of every stage and all four views | all |
| No input (File > New) | r2x's own | implemented | compared | newbeam-new |

Other sections under shear, from the brief's list:

| Item | Status | Case |
|---|---|---|
| T-beam with moment and shear | compared since 2026-11-21 | **tbeam-m2v** (A, the brief's) |
| I-girder at M/V = 1 m (the base of igirder-csoft9-mv and -csoft11-mv) | compared since 2026-11-21 | **igirder-mv** (B) |

---

## 3. What "scope complete" needs

Completion is judged against Response-2000 **as documented** (owner, 2026-11-22;
`docs/summary.md`, Aim and D17): the items marked "yes" in the Documented column. Judged
against this inventory, the scope is complete when

1. every documented item that reaches the analysis is built, with its rule and source in
   `docs/kernel.md`, unless it is out of scope by a decision of the owner's (hollow
   sections, long-term effects, strain discontinuity, the old text format; draped tendons,
   D4; the Hsu models with Tamai tension stiffening, D5). **Nothing documented is missing**
   (2026-11-22);
2. every such item has its case in `tests/oracle` or `tests/oracle/parked` and is reported
   when its set is run. The phase A set (the 17 load cases on Newbeam) is in `tests/oracle`;
   everything else is parked until phase B (D16, D19). One documented item has no case and
   cannot have one with r2x as it is: tension stiffening "None";
3. r2c refuses as out of scope what is out by design or **removed**, and treats as input
   errors the files Response itself rejects (D7).

**What was taken out on 2026-11-22** (D18, with D4, D5, D6, D10): compression softening 4,
16 and 17; the segmental curve for reinforcing steel; the reading of a tendon's drape; the
outline built for a shape given without one. r2c now refuses or rejects each. Five parked
fixtures need one of them and cannot be run by r2c: igirder-csoft4-m2v, igirder-csoft16-m2v,
igirder-csoft17-m2v, igirder-drape-m2v, newbeam-segsteel-m.

**Refused since 2026-11-22** (owner, D23): several sections in one file, and the horizontal
tie (stirrup pattern 7). Six more parked fixtures, all on Response's sample inputs, are
refused for it and kept: cm4-asis, liping-asis, marshall-asis, marshall-m, marshall-nonly,
se100-asis.

**Kept although not documented, by the owner's decision** (`docs/summary.md`):

- D21: the compression softening models the manual names and neither document gives a rule
  for (1, 3, 5 to 12, 14, 15). Their rules are the binary's.
- D22: compression softening 18, the default of Response 1.9.7, which is later than the
  manual. Every phase A case uses it.

A shrinkage profile of more than three points is documented (A-34: "parabolically
interpolates between these points") and has no case; the rule between points is r2c's
reading of that sentence.

### Items Response or r2x does not solve

The measurement says r2x does not solve these, so no case can be captured. What r2c does
with each was confirmed by the owner on 2026-11-22 (D6, D7).

- **Curved outline rows in an input file.** Response's XML reader rejects both forms. In
  the binary the words UP and DOWN are used by the reader of shape.dat (`004f96e0`) and by
  the width field of the outline dialog (`00448d90`) only; a circle defined in Response is
  saved as 13 straight rows (r2x's `quick-column/hand.r2t`). So a curved row never reaches
  the analysis. r2c rejects both forms as an input error, as Response does.
- **A shape without an outline.** Response opens the file with no concrete and the solve
  fails. r2c rejects the file as an input error (D6).
- **Tension stiffening "None"** needs an answer to Response's question that r2x does not
  give. r2c implements it (the thesis' base case; the manual, A-16). It stays not compared
  until r2x answers the question.
- **Tension stiffening 5**: Response refuses the file; so does r2c, as an input error.
- **`units="roman"`**: see the table. r2c rejects it as an input error.
- **Three load combinations on Newbeam** (table in section 2): they may solve on another
  section; not pursued.

### Questions for the owner

In `docs/summary.md`: D6 to D10 (answered 2026-11-22) and D21 to D23 (suggested).
T-headed stirrups are counted as compared already (section 1.6).
