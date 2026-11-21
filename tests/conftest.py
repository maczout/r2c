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
