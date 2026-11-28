# r2c

A Python reimplementation of the sectional analysis of Response-2000 (Bentz, University of
Toronto): the full response of a reinforced or prestressed concrete cross-section under axial
load, moment and shear, by the Modified Compression Field Theory.

r2c is the counterpart of [r2x](https://github.com/maczout/r2x), which drives Response-2000
itself. The two have the same command line and write the same record format, so one can stand
in for the other in a workflow, and r2x serves as the oracle that r2c is compared against.

**What it is signed off for** (the owner, a structural engineer, 2026-11-27; version 0.9.0):

- **Signed off: without shear** (moment, axial load, or both), as a stand-in for
  Response-2000.
- **Signed off: with shear, the control curves up to Response-2000's peak.** As far as
  Response's own response goes, r2c's curve is Response's.
- **Not signed off: strength with shear past Response-2000's last stage.** With shear
  Response often stops while the load is still rising. r2c sometimes carries on to a
  higher peak, and it cannot reliably tell you where Response stopped. Do not take r2c's
  peak with shear for Response's strength without reading "Known limitations".

**The numbers behind that, in one paragraph.** Without shear (moment, axial load, or both)
r2c gives Response-2000's answer: on sections it was never tuned against, every case was
inside ±5 % on every check, stage for stage. With shear, taking r2c's whole response as it
stands, the peak, the rising branch and the stress-state profiles were inside on 22 of 28
and 11 of 12 such cases; cut at Response's last stage where a trace of Response shows its
solve gave up there, on 26 of 28 and 12 of 12. The owner's target for this (93.4 %) is held
to the first reading, with no case cut, and is **not met**. The difference is that on about one
case in six r2c carries on to a higher peak than Response reports (see "Where r2c carried
on" and "Known limitations"). The shear-related profiles over the depth at the
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
| Record header | `r2x-version`, Response and Wine identification | `r2c-version`, `kernel: r2c`; with shear, where it applies, `carried-on-stage`, `carried-on-peak-stage`, `carried-on` or `ending` (see "Where r2c carried on") |
| Time, without shear | 25 to 75 s reading every stage | a second or two (faster on every case measured) |
| Time, with shear | about a minute reading every stage | one to several minutes: slower than r2x on most cases, up to about five times |
| With shear, where Response's solve gives up numerically before any failure | the response ends there, as Response's does | r2c carries on to a failure where its own copy of Response's solve fails too, and marks that stage in its record (see below); the mark is often not at Response's last stage |
| With shear, where Response refuses a state whose web is crushing | the response ends there | meant to end there too, with the reason in the record; on most such cases r2c does not see the crushing and goes on (a known limitation; the work is planned) |
| Inputs outside Response's manual that Response still solves | solved | refused (exit status 3) |

Charts have the same titles, units, number formats and row layout as Response's exports.
`docs/parity.md` lists every difference of interface found, and `docs/output.md` says what
a program that reads r2c's records may rely on from version 0.9.0.

## Where r2c carried on

With shear, Response-2000's response often ends while the load is still rising: its solve
of a load stage gives up, or it refuses a state whose web is crushing. r2c has its own
copy of that part of Response, and its record says what the copy did. It says what r2c
knows about its own run. **It does not say where Response itself stops.**

- `carried-on-stage: N` in the header (with `carried-on-peak-stage` and `carried-on`),
  and a section `carried-on/stage` with that stage's point on each control chart: after
  stage N r2c's copy of Response's solve failed on every try, and r2c carried on with its
  own solve. The stages after N are that solve's. `peak-stage` is the peak of the whole
  response; `carried-on-peak-stage` is the peak up to stage N.
- `ending: where r2c's copy of Response-2000's stage control stops: ...` in the header:
  the copy ran out of tries, r2c did not carry on, and the line says why (a state refused
  for a crushing web; a refusal that cannot be told from a failure of the solve; a
  failure beyond which r2c finds nothing either).
- Neither line: r2c's copy never ran out of tries. Response may still have stopped
  earlier than r2c did.

How good a guide the mark is to Response's last stage is under "Known limitations": not
a reliable one.

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
- **With shear, r2c's peak can stand above Response's, and the record does not reliably
  say so. This use is not signed off.** On sections that fail in flexure with some shear, Response's response often
  ends while the load is still rising: its solve gives up, or it refuses a state whose
  web is crushing. Up to that stage the two programs agree, and Response's figure is its
  repeatable answer. r2c is meant to carry on only past a numerical give-up, to mark that
  stage in its record, and to end where Response refuses a crushing web. It does so only
  in part, because it can mark only where its own copy of Response's solve fails, and
  the copy does not always fail where Response does. On the 40 cases with shear it was
  never tuned against, r2c went past Response's last stage on 15: the mark
  (`carried-on-stage`) is at that stage on 5, at a later or earlier stage on 5, and
  absent on 5; and on 2 of the 3 where Response refused a crushing web r2c went on. Its
  peak was 5 to 32 % above Response's on 6 of the 40. So: **the mark is unreliable as a
  sign of where Response stops.** Where the record has `carried-on-stage`, the peak up
  to it (`carried-on-peak-stage`) is the better guess at Response's strength, and it is
  a guess. Where it has not, do not take r2c's peak for Response's strength if the
  response has a sudden jump in load or a long tail of closely spaced stages. To know
  Response's strength with shear, run Response (r2x). Whether r2c's higher figure is
  the better answer has not been checked.
- **Where Response refuses a state whose web is crushing, r2c mostly does not see it**
  and goes on. The rule is read from the program and written, but it is switched off: as
  written it ends other cases too early. It is the first work planned on the
  calculation, after the gaps in the record (below) are closed.
- **The owner's target for the peak, rising branch and stress-state profiles with shear
  is not met**: 79 % and 92 % of the two sets of unseen cases, taking r2c's whole
  response, against 93.4 %.
- **The Shear Stress chart at the first stage (the initial load) has one line where
  Response's has two**; the missing one is zero unless the initial load has a shear
  (`docs/output.md` lists this and two smaller gaps in what the record carries). Closing
  the three is the first work planned after this version.
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
    docs/output.md         the record: what a program that reads it may rely on
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
