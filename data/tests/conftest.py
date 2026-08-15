"""Shared fixtures for the generator tests."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator.profiles import PROFILES  # noqa: E402


@pytest.fixture(params=sorted(PROFILES))
def profile_name(request: pytest.FixtureRequest) -> str:
    """Run a test once per profile."""
    return request.param
