"""Test ksef."""

import ksef


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(ksef.__name__, str)
