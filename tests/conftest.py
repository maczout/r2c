"""Shared fixtures: where the oracle records are, and Response's own folder if there is one."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ORACLE = Path(__file__).parent / "oracle"


@pytest.fixture(scope="session")
def oracle_dir() -> Path:
    return ORACLE


@pytest.fixture(scope="session")
def parked_dir() -> Path:
    """The fixtures parked until phase B (docs/summary.md, D16 and D19)."""
    return ORACLE / "parked"


@pytest.fixture(scope="session")
def response_dir() -> Path:
    """Response-2000's folder (for its sample inputs), from R2C_RESPONSE_DIR. They are not in
    this repository: they are part of Response."""
    d = os.environ.get("R2C_RESPONSE_DIR")
    if not d or not Path(d).is_dir():
        pytest.skip("R2C_RESPONSE_DIR is not set: Response's sample inputs are not available")
    return Path(d)


@pytest.fixture(scope="session")
def define_dirs() -> list[Path]:
    """Where the Quick Define inputs are (r2x's tests/reference/define), from R2C_DEFINE_DIR.
    They are r2x's, not this repository's; each is found by the SHA-256 its fixture records."""
    d = os.environ.get("R2C_DEFINE_DIR")
    if not d or not Path(d).is_dir():
        pytest.skip("R2C_DEFINE_DIR is not set: the Quick Define inputs are not available")
    return [Path(d)]


@pytest.fixture(scope="session")
def scope_dirs() -> list[Path]:
    """Where the inputs of the scope cases of increment S are, from R2C_SCOPE_DIR: the folder
    `python tools/variants.py R2C_SCOPE_DIR --inputs R2X/tests/reference` writes. They are
    derived from r2x's inputs and are not in this repository."""
    d = os.environ.get("R2C_SCOPE_DIR")
    if not d or not Path(d).is_dir():
        pytest.skip("R2C_SCOPE_DIR is not set: the inputs of the scope cases are not available")
    return [Path(d)]
