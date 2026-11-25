# Fixtures not run by default

Development cases that are captured but outside the set the default tools read (a tool given
`tests/oracle` reads that folder alone): the softening models on the I-girder, Response's
sample inputs as they come, and a few others. The developer has looked at all of them, so
none can be held out. Run them with

    python tools/verify.py tests/oracle/parked --inputs FOLDERS --out OUT --jobs N
    pytest -m parked
