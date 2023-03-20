"""Tests for token-based authorization."""
from requests import Request

from ksef.auth.token import TokenAuthorization


def test_enrich() -> None:
    """Test if simple enrichment works."""
    request = Request("POST", url="https://example.com")
    auth = TokenAuthorization(token="abc123")  # noqa: S106

    request = auth.modify_request(request)

    assert request.headers["Authorization"] == "abc123"
