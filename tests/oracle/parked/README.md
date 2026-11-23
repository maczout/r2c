# Parked fixtures

The oracle cases outside phase A (`docs/summary.md`, D16 and D19; owner, 2026-11-22): other
sections, other materials and reinforcement, units, material factors, More Detail, no input,
and Response's sample inputs. They are kept and not run by default; they come back in
phase B.

The development set is the fixtures directly in `tests/oracle` (`docs/summary.md`, "The
development set"): Newbeam with only its loads varied (17), the Quick Define sections (7,
step A-1) and the reinforcement varied (5, step A-2: moved from here on 2026-11-23). A tool
given `tests/oracle` reads that set alone, because the tools read one folder and not the
folders under it.

To run the parked set on request:

    python tools/verify.py tests/oracle/parked --inputs RESPONSE_FOLDER R2X/tests/reference SCOPE_INPUTS --out OUT --jobs N
    pytest -m parked                  # "parked and not slow" leaves out the parked shear cases
    python tools/capture.py ARCHIVE --from tests/oracle/parked ...

Five of them need something that was taken out on 2026-11-22 as beyond the documented scope
or out of scope (D4, D10, D18), and r2c now refuses their inputs: `igirder-drape-m2v`
(draped tendons), `igirder-csoft4-m2v`, `igirder-csoft16-m2v` and `igirder-csoft17-m2v`
(softening models that are not in the manual), `newbeam-segsteel-m` (a segmental curve for
reinforcing steel). Their fixtures are kept, as the record of what Response does.

Six more are refused since 2026-11-22 (D23) because Response's sample inputs hold several
sections in one file, which the manual does not have: `cm4-asis`, `liping-asis` (which has
horizontal ties besides, refused too), `marshall-asis`, `marshall-m`, `marshall-nonly` and
`se100-asis`. Their fixtures are kept (D19).
