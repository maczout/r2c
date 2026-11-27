# r2c's output: what a reader may rely on

**Stable for r2c 1.x.** This page is r2c's contract with whatever reads its records (r2
first). It says what is fixed for version 1, what is not, and where r2c's record differs
from r2x's. The framing is r2x's raw record format, version 1 (`docs/raw-format.md` in
r2x 0.5.0); `src/r2c/record.py` reads and writes it and is r2x's module, standard library
only.

## What r2c writes

One solve gives one record: `NAME.r2x.txt` in the output folder, or the same bytes on
standard output with `--stdout`. Nothing else is written. Progress and messages go to
standard error and are not part of the contract. Exit status: 0 solved, 1 failed, 2 usage
error, 3 input out of scope. A solve that fails or is refused leaves no record (the file
is written under a temporary name and renamed when complete).

## Fixed for 1.x

**Framing.** First line `r2x-raw 1`. Header lines `key: value`, an empty line, then
sections (`section NAME LENGTH`, LENGTH bytes, CRLF), then `end`. Every line ends in CRLF.
Read a record as bytes.

**Header keys**, in this order. Look them up by name.

| Key | Always | Meaning |
|---|---|---|
| `r2c-version` | yes | the version of r2c that wrote the record. **This key tells r2c's record from r2x's**, which has `r2x-version` instead |
| `kernel` | yes | `r2c` |
| `disclaimer` | yes | r2c's disclaimer, one line |
| `input-name` | yes | the input's file name, or `File > New` with no input (the built-in Newbeam) |
| `input-sha256` | with an input | SHA-256 of the input file's bytes |
| `units` | yes | `si`, `us` or `kgcm` |
| `factors` | yes | material factors in effect: concrete, steel, prestress; two decimals |
| `initial` | yes | initial load N, M, V in the units in effect; two decimals |
| `increment` | yes | load increment N, M, V; two decimals |
| `more-detail` | yes | the `--more-detail` value, `0` without |
| `views` | yes | detail views in the record, in catalogue order |
| `stage-count` | yes | load stages, numbered 0 to `stage-count` − 1; stage 0 is the initial load |
| `peak-stage` | yes | the stage with the largest load of the whole response, as r2x's key |
| `carried-on-stage` | where it applies | see "r2c's own lines" |
| `carried-on-peak-stage` | with `carried-on-stage` | the peak among stages 0 to `carried-on-stage` |
| `carried-on` | with `carried-on-stage` | what happened, in words |
| `ending` | where it applies | see "r2c's own lines" |
| `detail-stages` | yes | stages with detail-view sections, as numbers and ranges |

r2x's keys about its own machinery (`response-exe-sha256`, `response-files-sha256`,
`response-verified`, `wine-version`, `template-sha256`) are not in r2c's record.

**Sections.** The same names, order and bodies as r2x's:

- `control/KEY`: the control charts over all stages, one row per stage, row *i* being
  stage *i*. Which two (or one) there are follows the increment, as in r2x: `moment_ex`
  and `moment_phi`; `axial_ex` alone; `shear_gxy` with `moment_phi`, `axial_ex` or
  `shear_ex`.
- `stage/N/KEY`: for each stage N of `detail-stages`, every chart of the views in `views`,
  each once, in catalogue order. The 21 keys and their views are those of r2x's format
  page; the catalogue file `src/r2c/views.json` is r2x's own, item for item.
- Each body is text in the form of Response's Copy Chart Data: the same title line, axis
  titles with units, column heading, `Line type` and `New Line` lines, column count and
  printed decimals as Response's export of that chart in those units. Checked on every
  chart of every stage of the 182 development cases (`docs/output-check.md`, generated).

**Deterministic.** The same input, options and version give the same bytes on the same
machine. No timestamps or timings. Across machines a last printed digit may differ.

**With `--stage all`** every stage has its detail views. That is the record r2 should ask
for; without it only the peak stage has them (`--stage` takes r2x's values).

## r2c's own lines

With shear, r2c contains a copy of Response's control of load stages. Where that copy
runs out of tries, the record says what r2c did. These lines say what r2c knows about its
own run. **None of them says where Response-2000 itself stops**: measured against
Response, they sit at Response's last stage on about one case in three of those where
r2c goes past it (README, "Known limitations").

- `carried-on-stage: N`, `carried-on-peak-stage`, `carried-on` and a section
  `carried-on/stage`: after stage N every further try of r2c's copy of Response's solve
  failed numerically and r2c carried on with its own solve. Stages 0 to N are the copy's;
  the stages after N are r2c's own solve's. `peak-stage` is still the peak of the whole
  response. The section holds the stage number (a line `Stage : N`) and, for each
  control chart, a line `Chart : KEY`, that chart's column heading and stage N's row as
  the chart prints it. After More Detail, N is the stage's new number.
- `ending: where r2c's copy of Response-2000's stage control stops: REASON`: the copy ran
  out of tries and r2c did not carry on; the response ends there. The reasons are: a
  state refused for a crushing web; a refusal that cannot be told from a failure of the
  solve; a failure with the load already under 0.8 of the largest; a failure beyond
  which r2c's own solve finds nothing either.
- Neither: the response ended by the tests r2c has of Response's own (a fall of load,
  rupture, crushing), or without shear.

Fixed for 1.x: the keys, when they are present, the meaning of N, the section's name and
the three kinds of line in it. A reader that takes every section for a chart must skip
`carried-on/stage`; one that looks sections up by name is not affected.

## Not fixed

- **The values.** A later version may compute a different response for the same input.
  What 1.0.0 gives is described in the README ("Known limitations") and measured in
  `docs/verification-results.md`.
- **How many stages there are and where they are.** r2c's stage *i* is not Response's
  stage *i* except at stage 0. A comparison of the two programs should match stages by
  their place on the control curve, not by number (`tools/compare.py` does it that way;
  `docs/measures.md`).
- **How many rows a chart has.** r2c layers the section as Response does, but the rows
  of a profile can differ in number.
- **The wording** of `disclaimer`, of `carried-on` and of the reason after `ending`'s
  fixed lead. Do not parse them.
- **Messages on standard error**, and anything under `tools/`.

## Versioning

r2c follows semantic versioning from 1.0.0, with this page as the public interface. A
change to anything under "Fixed for 1.x" needs 2.0.0; a new header key or a new kind of
section is a minor version, and readers ignore keys and sections they do not know. A
change of the framing raises the record format's own number on the first line, as in
r2x. A release that changes results says so in its notes.

## What r2x's record carries that r2c's does not

Found by `python tools/carries.py ARCHIVE VERIFY_OUT`, which sets r2x's whole capture of
each development case beside r2c's whole record, every stage and every chart
(`docs/output-check.md`; no values are compared there). Every control chart and all 21
detail charts are present at every stage, with Response's headings, units, lines and
number formats, except:

1. **The Shear Stress chart at stage 0 has one line in r2c's record and two in
   Response's.** Response's second line (line type 2) is there at the initial load in
   every case. It is zero throughout unless the initial load has a shear. r2c writes the
   second line from stage 1 on where the increment has a shear, as Response does.
2. **An initial shear with no shear in the increment**: Response keeps the second line
   of the Shear Stress chart, with values, beyond stage 0; r2c's record never has it (one
   development case, Newbeam under a constant shear of 50 kN with a rising moment).
3. **An increment of 0,0,0** (two stages, both at the initial load): at stage 1
   Response's Shear Strain and Transverse Strain charts are a single plain line; r2c's
   have the envelope lines as well (one development case).
4. **`--report`** (r2x's page of screenshots of Response's windows) and r2x's `define`
   are not in r2c, by the owner's decision of 2026-11-24. They carry no data.

`input-sha256` shows as missing in `docs/output-check.md` on the cases solved from r2c's
built-in Newbeam by `tools/verify.py`; `r2c solve FILE` always writes it.

Neither program's record has what Response shows only as pictures: the cross section, the
crack diagram, the internal forces and the N+M cell of each nine-chart view.
