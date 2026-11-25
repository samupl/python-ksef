"""Tests for the Client HTTP timeout."""
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from ksef.auth.base import Authorization
from ksef.client import DEFAULT_CLIENT_TIMEOUT, Client
from ksef.constants import Environment

CUSTOM_TIMEOUT = 42
PER_REQUEST_TIMEOUT = 7


def _client(**kwargs: Any) -> Client:
    auth = MagicMock(spec=Authorization)
    auth.get_access_token.return_value = "test-token"
    return Client(authorization=auth, environment=Environment.TEST, **kwargs)


def _sent_timeout(client: Client) -> object:
    """Make one request through the client's session and return the timeout it used."""
    with patch.object(requests.Session, "request") as request:
        request.return_value = MagicMock(status_code=200)
        client.session.get("https://example.invalid/")
    return request.call_args.kwargs["timeout"]


def test_default_timeout_is_applied() -> None:
    """Without an explicit timeout, every request uses DEFAULT_CLIENT_TIMEOUT."""
    client = _client()

    assert client.timeout == DEFAULT_CLIENT_TIMEOUT
    assert _sent_timeout(client) == DEFAULT_CLIENT_TIMEOUT


@pytest.mark.parametrize("timeout", [300, 12.5, (5, 300), None])
def test_custom_timeout_is_applied(timeout: object) -> None:
    """The timeout passed to Client is sent as-is, including tuples and None."""
    client = _client(timeout=timeout)

    assert _sent_timeout(client) == timeout


def test_explicit_per_request_timeout_wins() -> None:
    """A timeout given for a single request overrides the client default."""
    client = _client(timeout=300)

    with patch.object(requests.Session, "request") as request:
        request.return_value = MagicMock(status_code=200)
        client.session.get("https://example.invalid/", timeout=PER_REQUEST_TIMEOUT)

    assert request.call_args.kwargs["timeout"] == PER_REQUEST_TIMEOUT


def test_api_methods_use_the_client_timeout() -> None:
    """A real API method (not just the raw session) sends the configured timeout."""
    client = _client(timeout=CUSTOM_TIMEOUT)
    response = MagicMock(status_code=200)
    response.json.side_effect = ValueError("stop after the request")

    with patch.object(requests.Session, "request", return_value=response) as request, pytest.raises(
        ValueError, match="stop after the request"
    ):
        client.get_session_status("SESSION-1")

    assert request.call_args.kwargs["timeout"] == CUSTOM_TIMEOUT


def test_timeout_error_propagates() -> None:
    """A timeout surfaces as requests.Timeout so callers can classify it."""
    client = _client(timeout=1)

    with patch.object(
        requests.Session, "send", side_effect=requests.ReadTimeout("timed out")
    ), pytest.raises(requests.ReadTimeout):
        client.session.get("https://example.invalid/")
