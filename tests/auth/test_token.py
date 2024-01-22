"""Tests for token-based authorization."""
from urllib.parse import urljoin

from requests import Request
from responses import RequestsMock

from ksef.auth.token import TokenAuthorization
from ksef.constants import BASE_URL, URL_AUTH_CHALLENGE
from ksef.models.responses.authorization_challenge import AuthorizationChallenge


def test_enrich() -> None:
    """Test if simple enrichment works."""
    request = Request("POST", url="https://example.com")
    auth = TokenAuthorization(token="abc123", public_key="irrelevant")  # noqa: S106

    request = auth.modify_request(request)

    assert request.headers["SessionToken"] == "abc123"


def test_get_authorization_challenge(mocked_responses: RequestsMock) -> None:
    """Test if getting authorization challenge works."""
    timestamp = "2023-03-20T10:02:54.960Z"
    challenge_digest = "20230320-CR-3B5DCC20B3-C026645D90-3C"
    mocked_responses.add(
        url=urljoin(BASE_URL, URL_AUTH_CHALLENGE),
        method="POST",
        content_type="application/json",
        json={
            "timestamp": timestamp,
            "challenge": challenge_digest,
        },
    )
    auth = TokenAuthorization(
        token="abc123",  # noqa: S106
        base_url=BASE_URL,
        public_key="irrelevant",
    )
    challenge = auth.get_authorization_challenge(nip="1234567890")

    assert isinstance(challenge, AuthorizationChallenge)
    assert challenge.challenge == challenge_digest
    assert challenge.timestamp == timestamp
