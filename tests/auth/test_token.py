"""Tests for token-based authorization (API v2)."""
import base64
import datetime

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
    generate_private_key,
)
from cryptography.x509.oid import NameOID
from responses import RequestsMock

from ksef.auth.token import TokenAuthorization
from ksef.constants import (
    URL_AUTH_CHALLENGE,
    URL_AUTH_KSEF_TOKEN,
    URL_AUTH_STATUS,
    URL_AUTH_TOKEN_REDEEM,
    URL_PUBLIC_KEY_CERTS,
    Environment,
)
from ksef.exceptions import UnsupportedResponseError
from ksef.models.responses.auth import AuthChallenge

_TEST_TIMESTAMP = 1700000000000


def _generate_test_cert() -> tuple[RSAPrivateKey, RSAPublicKey, str]:
    """Generate a self-signed certificate and key pair for testing."""
    private_key = generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    cert_b64 = base64.b64encode(cert_der).decode("ascii")
    return private_key, public_key, cert_b64


BASE = Environment.TEST.value


def test_get_challenge(mocked_responses: RequestsMock) -> None:
    """Test getting the authorization challenge."""
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_CHALLENGE}",
        method="POST",
        content_type="application/json",
        json={
            "challenge": "test-challenge-digest",
            "timestampMs": _TEST_TIMESTAMP,
        },
    )
    auth = TokenAuthorization(
        token="abc123",  # noqa: S106
        environment=Environment.TEST,
    )
    challenge = auth._get_challenge()

    assert isinstance(challenge, AuthChallenge)
    assert challenge.challenge == "test-challenge-digest"
    assert challenge.timestamp_ms == _TEST_TIMESTAMP


def test_encrypt_token() -> None:
    """Test RSA-OAEP encryption of the token."""
    private_key, public_key, _cert_b64 = _generate_test_cert()

    auth = TokenAuthorization(
        token="my-ksef-token",  # noqa: S106
        environment=Environment.TEST,
    )
    challenge = AuthChallenge(challenge="test-challenge", timestamp_ms=_TEST_TIMESTAMP)
    encrypted = auth._encrypt_token(
        challenge=challenge,
        public_key=public_key,
    )
    encrypted_bytes = base64.b64decode(encrypted)

    decrypted = private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    assert decrypted == b"my-ksef-token|1700000000000"


def test_authorize_full_flow(mocked_responses: RequestsMock) -> None:
    """Test the full authorization flow: certs -> challenge -> ksef-token -> poll -> redeem."""
    _private_key, _public_key, cert_b64 = _generate_test_cert()

    # 1. Mock GET /security/public-key-certificates
    mocked_responses.add(
        url=f"{BASE}{URL_PUBLIC_KEY_CERTS}",
        method="GET",
        content_type="application/json",
        json=[
            {
                "certificate": cert_b64,
                "usage": ["KsefTokenEncryption"],
            }
        ],
    )

    # 2. Mock POST /auth/challenge
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_CHALLENGE}",
        method="POST",
        content_type="application/json",
        json={
            "challenge": "flow-challenge",
            "timestampMs": _TEST_TIMESTAMP,
        },
    )

    # 3. Mock POST /auth/ksef-token
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_KSEF_TOKEN}",
        method="POST",
        content_type="application/json",
        json={
            "referenceNumber": "ref-123",
            "authenticationToken": {
                "token": "auth-token-abc",
                "validUntil": "2024-01-01T00:00:00Z",
            },
        },
    )

    # 4. Mock GET /auth/{referenceNumber} (poll — immediately ready)
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_STATUS.format(reference_number='ref-123')}",
        method="GET",
        content_type="application/json",
        json={
            "status": {"code": 200, "description": "OK"},
            "isTokenRedeemed": False,
        },
    )

    # 5. Mock POST /auth/token/redeem
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_TOKEN_REDEEM}",
        method="POST",
        content_type="application/json",
        json={
            "accessToken": {
                "token": "access-token-xyz",
                "validUntil": "2024-01-01T01:00:00Z",
            },
            "refreshToken": {
                "token": "refresh-token-xyz",
                "validUntil": "2024-01-02T00:00:00Z",
            },
        },
    )

    auth = TokenAuthorization(
        token="my-ksef-token",  # noqa: S106
        environment=Environment.TEST,
    )
    tokens = auth.authorize(nip="1234567890")

    assert tokens.access_token.token == "access-token-xyz"  # noqa: S105
    assert tokens.refresh_token.token == "refresh-token-xyz"  # noqa: S105
    assert auth.get_access_token() == "access-token-xyz"


def test_authorize_error_on_challenge(mocked_responses: RequestsMock) -> None:
    """Test error handling when challenge request fails."""
    _private_key, _public_key, cert_b64 = _generate_test_cert()

    mocked_responses.add(
        url=f"{BASE}{URL_PUBLIC_KEY_CERTS}",
        method="GET",
        content_type="application/json",
        json=[
            {
                "certificate": cert_b64,
                "usage": ["KsefTokenEncryption"],
            }
        ],
    )

    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_CHALLENGE}",
        method="POST",
        content_type="application/json",
        json={"error": "bad request"},
        status=400,
    )

    auth = TokenAuthorization(
        token="my-ksef-token",  # noqa: S106
        environment=Environment.TEST,
    )

    with pytest.raises(UnsupportedResponseError, match="400"):
        auth.authorize(nip="1234567890")
