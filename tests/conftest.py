"""Global configuration for all tests."""
from typing import Generator

import pytest
import responses


@pytest.fixture()
def mocked_responses() -> Generator[responses.RequestsMock, None, None]:
    """Pytest-compatible fixture for responses."""
    with responses.RequestsMock() as rsps:
        yield rsps
