# r2c

A Python reimplementation of the sectional analysis of Response-2000 (Bentz, University of
Toronto): the full response of a reinforced or prestressed concrete cross-section under axial
load, moment and shear, by the Modified Compression Field Theory.

r2c is the counterpart of [r2x](https://github.com/maczout/r2x), which drives Response-2000
itself. The two have the same command line and write the same record format, so one can stand
in for the other in a workflow, and r2x serves as the oracle that r2c is compared against.

**What it is good for, in one paragraph.** Without shear (moment, axial load, or both)
r2c gives Response-2000's answer: on sections it was never tuned against, every case was
inside ±5 % on every check, stage for stage. With shear it gives Response's curve up to
the peak (the peak load, the rising branch, the stress state under moment and axial load,
the crack widths) on every such case; the shear-related profiles over the depth at the
peak, and how the response ends after it, agree on about three cases in five and three in
four, and there Response does not agree with itself either when an input changes by next
to nothing. The numbers, the cases they were measured on and an independent assessor's
findings are in `docs/summary.md`; https://maczout.github.io/r2c/ shows the development
results as pictures. Read "Known limitations" below before relying on a result.

r2c is not affiliated with the authors of Response-2000 and does not check designs. Its results
are its own; the engineer who uses them is responsible for that use.

## Install

    git clone https://github.com/maczout/r2c
    cd r2c
    pip install -e .          # Python 3.10 or later; needs numpy and nothing else

Nothing of Response-2000 is needed to run r2c, and nothing of it is in this repository.

## Use

    r2c solve                              # Response's default section (Newbeam), moment only
    r2c solve beam.rsp                     # an input saved by Response-2000 (.rsp or .r2t)
    r2c solve beam.rsp --increment 0,1,1   # N, M, V increments: here M/V = 1 m
    r2c solve beam.rsp --initial=-500,0,0 --increment 0,1,1 --stage all --out results
    r2c solve --help

The section itself is drawn and saved in Response-2000 (or written as its XML); r2c reads
that file and never edits it. Loads are N, M, V: tension positive, compression on top
positive; only the signs and ratio of an increment matter. A negative value needs the `=`
form (`--initial=-500,0,0`).

Each input gives one record, `NAME.r2x.txt`, in the output folder: the control charts over all
load stages and the detail-view charts of the stages asked for, as text in the form of
Response's own "Copy Chart Data". The options are r2x's: `--units`, `--factors`, `--initial`,
`--increment`, `--more-detail`, `--stage`, `--views`, `--out`, `--stdout`, `--overwrite`, `-p`,
`-q`. Exit status: 0 solved, 1 failed, 2 usage error, 3 input out of scope.

## How it differs from r2x

[r2x](https://github.com/maczout/r2x) runs Response-2000 itself (under Wine) and reads its
charts; r2c computes the response with its own kernel, written from the thesis and from
how the program itself calculates. The command line and the record are the same, so one
can stand in for the other.

| | r2x | r2c |
|---|---|---|
| What solves | Response-2000 1.9.7 under Wine | r2c's own kernel (Python, numpy) |
| Needs | Response-2000, Wine | nothing else |
| `solve` | as above | same options, same record format |
| `--report` | Response's report pages | not available (usage error) |
| `define`, sessions, `setup` | yes | no |
| `health` | checks Wine and Response | prints the version |
| Record header | `r2x-version`, Response and Wine identification | `r2c-version`, `kernel: r2c` |
| Time, without shear | 25 to 75 s reading every stage | a second or two (faster on every case measured) |
| Time, with shear | about a minute reading every stage | one to several minutes: slower than r2x on most cases, up to about five times |
| With shear, where Response's solve gives up before any failure | the response ends there, as Response's does | r2c carries on to a failure (see below) |
| Inputs outside Response's manual that Response still solves | solved | refused (exit status 3) |

Charts have the same titles, units, number formats and row layout as Response's exports.
`docs/parity.md` lists every difference of interface found.

## Scope

In: Response-2000 as documented in its manual (Appendix A of Bentz's thesis). Sections
Response-2000 saves as XML (`.rsp`, `.r2t`): any solid outline, several concrete types, bars
and tendons, stirrups; the base curves, compression softening and tension stiffening models
the manual names; shrinkage and thermal strains; SI, US and kg-cm units; CSA material factors;
More Detail. `docs/scope.md` lists every input and where r2c stands on it.

Out (exit status 3): the older text format (`Ver_0.8`), hollow sections, long-term effects
(creep, relaxation), strain discontinuity, draped tendons, the Hsu softening models with Tamai
tension stiffening, tension stiffening turned off, what is not in the manual (compression
softening 4, 16 and 17, a segmental curve for reinforcing steel), and what r2x also leaves
out: interaction diagrams, member response, pushover. What Response itself rejects is an
input error: curved outline rows in a file, a shape without an outline. Negative shear is
refused, as in Response.

## Known limitations

In plain language; `docs/deviations.md` has the full list and `docs/summary.md` the
numbers.

- **With shear, the profiles over the depth at the peak can differ from Response's by
  more than 5 %** (shear stress and strain, shear on the crack, principal tension,
  stirrup and bond charts), on about two cases in five, while the peak load and the curve
  up to it agree. Near a flat peak the two programs settle on slightly different states.
  Response itself does not hold these profiles when a concrete strength changes by a
  twentieth of a per cent. Use the peak and the curve; treat a profile at the peak of a
  shear response as indicative.
- **With shear, the response after the peak and where it ends** differ from Response's on
  about one case in four. This was the lowest priority and was not worked on.
- **With shear, r2c carries on where Response stops early.** On sections that fail in
  flexure with some shear, Response's solve often gives up while the load is still
  rising, and its response ends there with no failure. r2c finds further states and can
  reach a peak several per cent higher than Response reports. Up to Response's last
  stage the two agree. This is deliberate (the owner's decision); if you need Response's
  number, it is the load at Response's last stage, not r2c's peak.
- **A circular column, or any section that stays uniform, under axial load alone:** after
  the peak r2c keeps a uniform response and Response does not. Deliberate.
- **With shear r2c is slow**: minutes for a case, longer than r2x on most.
- **Some inputs Response solves are refused** (the "Out" list above), and four kinds of
  input on which Response gives up part-way are solved by r2c.
- **The number and place of load stages can differ from Response's after the peak**, and
  in a few places before it (a section cracked from the start; More Detail at its most).
  The curves agree; the stages are not the same ones.
- r2c was checked against Response-2000 1.9.7 only, on rectangular beams, a T-beam, a
  circular column, a prestressed I-girder, slab strips and five of Response's sample
  sections. A section unlike all of these has not been checked.

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
    tools/dashboard.py     the results pages: how accurate r2c is, and the details (CI publishes them)
    tools/diagnose.py      r2c at Response's strain states, and along its control values
    tools/decompile.py     a routine of Response's binary, from a Ghidra project kept elsewhere
    tools/capture.py       rebuild the archive of full oracle captures with r2x
    tools/check.py         checks before pushing: the record follows the brief
    tools/heldout.py       the held-out sets: their recipe, their capture, their totals-only scorer
    tests/oracle/          the development set: records captured from Response-2000 with r2x
    tests/oracle/parked/   more development cases, not run by default
    heldout/               the two held-out sets: the frozen manifests and the totals
    docs/kernel.md         what the kernel does and where each rule comes from
    docs/verification-results.md   the results, generated
    docs/brief.md          the owner's brief: the goal, the priorities, the rules
    docs/summary.md        the sign-off page: what r2c is good for, the held-out totals, the assessor's findings
    docs/assessment.md     the independent assessor's findings, with the developer's answers
    docs/measures.md       how a result is judged: the tolerances and the checks
    docs/deviations.md     known deviations, in plain language
    docs/status.md         where the work stands, for the developer
    docs/log/              one log per increment
    CLAUDE.md              how work on r2c is done (for people and coding agents)

## Tests

    pytest                 # fast cases
    pytest -m slow         # shear cases, a minute or more each
    R2C_RESPONSE_DIR=/path/to/Response pytest     # also Response's own sample inputs

Response-2000 and its sample files are not in this repository.

## Licence

MIT (see LICENSE). Response-2000 is the work of Evan Bentz and Michael Collins; this project
contains none of its code or files.
