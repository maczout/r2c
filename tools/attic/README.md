# tools/attic

Scripts that answered a question once and are not in use. They are not maintained and not
tested: each was written to sit in `tools/` and import its neighbours from there, so run one
with `PYTHONPATH=tools python tools/attic/NAME.py`, and expect to repair it first. Names of
decisions and phases in their docstrings belong to the earlier record (`docs/history.md`).

`evidence.py` gathered, for each deviation, the evidence an independent assessor was given.
The finishing assessment of the brief will want the same thing; start from it.
