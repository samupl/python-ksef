"""Integration tests for XAdES certificate authentication."""
import pytest

from ksef.auth.xades import XadesAuthorization


@pytest.mark.integration()
@pytest.mark.withoutresponses()
def test_xades_authenticate(
    xades_authorization: XadesAuthorization,
    nip: str,
) -> None:
    """Authenticate with an XAdES-signed request and verify we receive valid tokens."""
    tokens = xades_authorization.authorize(nip=nip)

    assert tokens.access_token.token, "Expected a non-empty access token"
    assert tokens.refresh_token.token, "Expected a non-empty refresh token"
    assert xades_authorization.get_access_token() == tokens.access_token.token
