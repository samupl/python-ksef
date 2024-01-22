"""Test the utilities module."""
import pytest

from ksef.utils import camelcase_to_words


@pytest.mark.parametrize(
    ("value", "expected_value"),
    [
        ("Test", "Test"),
        ("TestTest", "Test test"),
    ],
)
def test_camelcase_to_words(value: str, expected_value: str) -> None:
    """Test the camelcase_to_words function."""
    assert camelcase_to_words(value) == expected_value
