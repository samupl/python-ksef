"""Tests for XAdES signature-based authorization (API v2)."""
import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.x509.oid import NameOID
from lxml import etree
from responses import RequestsMock

from ksef.auth.xades import XadesAuthorization
from ksef.constants import (
    URL_AUTH_CHALLENGE,
    URL_AUTH_STATUS,
    URL_AUTH_TOKEN_REDEEM,
    URL_AUTH_XADES_SIGNATURE,
    Environment,
)
from ksef.models.responses.auth import AuthChallenge

_TEST_TIMESTAMP = 1700000000000


def _generate_self_signed_cert() -> tuple[bytes, bytes]:
    """Generate a self-signed certificate and private key for testing."""
    private_key = generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "Test Certificate"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return cert_pem, key_pem


BASE = Environment.TEST.value


def test_build_and_sign_request() -> None:
    """Test that the XML document is well-formed and contains a signature."""
    cert_pem, key_pem = _generate_self_signed_cert()
    auth = XadesAuthorization(
        signing_cert=cert_pem,
        private_key=key_pem,
        environment=Environment.TEST,
    )

    challenge = AuthChallenge(challenge="test-challenge-xades", timestamp_ms=_TEST_TIMESTAMP)
    signed_xml = auth._build_and_sign_request(challenge=challenge, nip="1234567890")

    root = etree.fromstring(signed_xml)  # noqa: S320
    ns_auth = "http://ksef.mf.gov.pl/auth/token/2.0"

    # Check root element
    assert "AuthTokenRequest" in root.tag

    # Check Challenge element
    challenge_el = root.find(f"{{{ns_auth}}}Challenge")
    assert challenge_el is not None
    assert challenge_el.text == "test-challenge-xades"

    # Check ContextIdentifier
    ctx = root.find(f"{{{ns_auth}}}ContextIdentifier")
    assert ctx is not None
    assert ctx.find(f"{{{ns_auth}}}Nip").text == "1234567890"

    # Check SubjectIdentifierType
    sit = root.find(f"{{{ns_auth}}}SubjectIdentifierType")
    assert sit is not None
    assert sit.text == "certificateSubject"

    # Check Signature element exists
    ns_ds = "http://www.w3.org/2000/09/xmldsig#"
    sig = root.find(f"{{{ns_ds}}}Signature")
    assert sig is not None

    # Check SignatureValue is populated
    sig_val = sig.find(f"{{{ns_ds}}}SignatureValue")
    assert sig_val is not None
    assert sig_val.text is not None
    assert len(sig_val.text) > 0


def test_authorize_full_flow(mocked_responses: RequestsMock) -> None:
    """Test the full XAdES authorization flow."""
    cert_pem, key_pem = _generate_self_signed_cert()

    # 1. Mock POST /auth/challenge
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_CHALLENGE}",
        method="POST",
        content_type="application/json",
        json={
            "challenge": "xades-challenge",
            "timestampMs": _TEST_TIMESTAMP,
        },
    )

    # 2. Mock POST /auth/xades-signature
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_XADES_SIGNATURE}",
        method="POST",
        content_type="application/json",
        json={
            "referenceNumber": "xades-ref-456",
            "authenticationToken": {
                "token": "xades-auth-token",
                "validUntil": "2024-01-01T00:00:00Z",
            },
        },
    )

    # 3. Mock GET /auth/{referenceNumber} (immediately ready)
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_STATUS.format(reference_number='xades-ref-456')}",
        method="GET",
        content_type="application/json",
        json={
            "status": {"code": 200, "description": "OK"},
            "isTokenRedeemed": False,
        },
    )

    # 4. Mock POST /auth/token/redeem
    mocked_responses.add(
        url=f"{BASE}{URL_AUTH_TOKEN_REDEEM}",
        method="POST",
        content_type="application/json",
        json={
            "accessToken": {
                "token": "xades-access-token",
                "validUntil": "2024-01-01T01:00:00Z",
            },
            "refreshToken": {
                "token": "xades-refresh-token",
                "validUntil": "2024-01-02T00:00:00Z",
            },
        },
    )

    auth = XadesAuthorization(
        signing_cert=cert_pem,
        private_key=key_pem,
        environment=Environment.TEST,
    )
    tokens = auth.authorize(nip="1234567890")

    assert tokens.access_token.token == "xades-access-token"  # noqa: S105
    assert tokens.refresh_token.token == "xades-refresh-token"  # noqa: S105
    assert auth.get_access_token() == "xades-access-token"
