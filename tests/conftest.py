"""Global configuration for all tests."""
import pytest
import responses


@pytest.fixture()
def mocked_responses() -> responses.RequestsMock:
    """Pytest-compatible fixture for responses."""
    with responses.RequestsMock() as rsps:
        yield rsps
