# Parked fixtures

The oracle cases outside phase A (`docs/summary.md`, D16 and D19; owner, 2026-11-22): other
sections, other materials and reinforcement, units, material factors, More Detail, no input,
and Response's sample inputs. They are kept and not run by default; they come back in
phase B.

The phase A set is the 17 fixtures directly in `tests/oracle`: Newbeam with only its loads
varied. A tool given `tests/oracle` reads that set alone, because the tools read one folder
and not the folders under it.

To run the parked set on request:

    python tools/verify.py tests/oracle/parked --inputs RESPONSE_FOLDER R2X/tests/reference SCOPE_INPUTS --out OUT --jobs N
    pytest -m parked                  # "parked and not slow" leaves out the parked shear cases
    python tools/capture.py ARCHIVE --from tests/oracle/parked ...
