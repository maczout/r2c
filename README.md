# r2c

A Python reimplementation of the sectional analysis of Response-2000 (Bentz, University of
Toronto): the full response of a reinforced or prestressed concrete cross-section under axial
load, moment and shear, by the Modified Compression Field Theory.

r2c is the counterpart of [r2x](https://github.com/maczout/r2x), which drives Response-2000
itself. The two have the same command line and write the same record format, so one can stand
in for the other in a workflow, and r2x serves as the oracle that r2c is compared against.

**Status: 0.1.0, a first pass.** Flexure and axial load follow Response closely, stage for
stage in most cases. Shear follows it up to the peak in the cases tried, and less well after
it; some shear responses end early. `docs/verification-results.md` has the numbers, case by case, and
`docs/verification.md` what they mean and what falls short; https://maczout.github.io/r2c/
shows the same results as pictures. Read both before relying on a
result.

r2c is not affiliated with the authors of Response-2000 and does not check designs. Its results
are its own; the engineer who uses them is responsible for that use.

## Install

    pip install -e .          # Python 3.10 or later; needs numpy

## Use

    r2c solve                              # Response's default section (Newbeam), moment only
    r2c solve beam.rsp                     # an input saved by Response-2000 (.rsp or .r2t)
    r2c solve beam.rsp --increment 0,1,1   # N, M, V increments: here M/V = 1 m
    r2c solve beam.rsp --initial=-500,0,0 --increment 0,1,1 --stage all --out results
    r2c solve --help

Each input gives one record, `NAME.r2x.txt`, in the output folder: the control charts over all
load stages and the detail-view charts of the stages asked for, as text in the form of
Response's own "Copy Chart Data". The options are r2x's: `--units`, `--factors`, `--initial`,
`--increment`, `--more-detail`, `--stage`, `--views`, `--out`, `--stdout`, `--overwrite`, `-p`,
`-q`. Exit status: 0 solved, 1 failed, 2 usage error, 3 input out of scope.

### Differences from r2x

| | r2x | r2c |
|---|---|---|
| What solves | Response-2000 1.9.7 under Wine | r2c's own kernel |
| `solve` | as above | same options and record |
| `--report` | Response's report pages | not available (usage error) |
| `define`, sessions, `setup` | yes | no |
| `health` | checks Wine and Response | prints the version |
| Record header | `r2x-version`, Response and Wine identification | `r2c-version`, `kernel: r2c` |
| Time for a solve | a few seconds, mostly starting Response under Wine (4.3 s for the Newbeam, moment only, peak-only capture); 25 to 75 s with `--stage all`, nearly all of it reading charts | 1 to 20 s without shear; 1.5 to 4 min with shear |

Charts have the same titles, units, number formats and row layout as Response's exports. The
numbers differ where the kernel differs (docs/verification.md), and the number of load stages
can differ after the peak.

### Scope

In: sections Response-2000 saves as XML (`.rsp`, `.r2t`): any solid outline, several concrete
types, bars and tendons, stirrups; the base curves, compression softening and tension
stiffening models of Response; SI, US and kg-cm units; CSA material factors; More Detail.

Out (exit status 3): the older text format (`Ver_0.8`), hollow sections, long-term effects
(shrinkage, creep, relaxation, thermal strains), strain discontinuity, and what r2x also leaves
out: interaction diagrams, member response, pushover. Curved outline segments are read as
straight. Negative shear is refused, as in Response.

## Layout

    src/r2c/inputs.py      reads the input
    src/r2c/materials.py   concrete and steel relations
    src/r2c/section.py     geometry, crack spacing and bond tables
    src/r2c/node.py        MCFT at a point, with the crack check
    src/r2c/solver.py      forces of a strain state, layering, the flexure and axial driver
    src/r2c/shear.py       shear: longitudinal stiffness method and its driver
    src/r2c/export.py      the charts, in Response's text form
    src/r2c/run.py, cli.py the solve and the command line
    tools/compare.py       compare two records (either may be r2x's or r2c's)
    tools/verify.py        run r2c on a set of reference records and compare
    tools/trim.py          cut a record down to a test fixture
    tools/report.py        write docs/verification-results.md from a verify run
    tools/dashboard.py     the results as one HTML page (published by CI with GitHub Pages)
    tools/diagnose.py      r2c at Response's strain states, and along its control values
    tools/decompile.py     a routine of Response's binary, from a Ghidra project kept elsewhere
    tools/capture.py       rebuild the archive of full oracle captures with r2x
    tools/check.py         checks before pushing: results current, docs as generated
    tests/oracle/          records captured from Response-2000 with r2x: the phase A set
    tests/oracle/parked/   the cases parked until phase B; not run by default
    docs/kernel.md         what the kernel does and where each rule comes from
    docs/verification.md   r2c against Response-2000: what the results mean
    docs/verification-results.md   the results, generated
    docs/acceptance.md     what counts as agreement (tolerances)
    docs/status.md         where the work stands, options for next steps
    docs/log/              one log per working session
    CLAUDE.md              how work on r2c is done (for people and coding agents)

## Tests

    pytest                 # fast cases
    pytest -m slow         # shear cases, a minute or more each
    R2C_RESPONSE_DIR=/path/to/Response pytest     # also Response's own sample inputs

Response-2000 and its sample files are not in this repository.

## Licence

MIT (see LICENSE). Response-2000 is the work of Evan Bentz and Michael Collins; this project
contains none of its code or files.
