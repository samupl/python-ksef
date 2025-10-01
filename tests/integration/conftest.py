"""Integration tests configuration file."""
import pytest


@pytest.fixture()
def client() -> "ksef.client.Client":  # type: ignore[name-defined]  # noqa: F821
    """KSEF Client with token authorization."""
    from ksef.auth.token import TokenAuthorization
    from ksef.client import Client

    authorization = TokenAuthorization(
        token="", public_key="", base_url="https://ksef-test.mf.gov.pl/api/v2/"
    )
    authorization.authorize(nip="1234567890")
    return Client(
        authorization=authorization,
    )
