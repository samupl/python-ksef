"""Integration tests for KSeF Token authentication."""
import pytest

from ksef.auth.token import TokenAuthorization
from ksef.constants import Environment


@pytest.mark.integration()
@pytest.mark.withoutresponses()
def test_token_authenticate(
    token_authorization: TokenAuthorization,
    nip: str,
) -> None:
    """Authenticate with a KSeF token and verify we receive valid tokens."""
    tokens = token_authorization.authorize(nip=nip)

    assert tokens.access_token.token, "Expected a non-empty access token"
    assert tokens.refresh_token.token, "Expected a non-empty refresh token"
    assert token_authorization.get_access_token() == tokens.access_token.token


@pytest.mark.integration()
@pytest.mark.withoutresponses()
def test_token_challenge_reachable(
    ksef_token: str,
    environment: Environment,
) -> None:
    """Verify we can reach the challenge endpoint on the test environment."""
    auth = TokenAuthorization(token=ksef_token, environment=environment)
    challenge = auth._get_challenge()

    assert challenge.challenge, "Expected a non-empty challenge string"
    assert challenge.timestamp_ms > 0, "Expected a positive timestamp"
