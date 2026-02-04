"""Integration tests configuration file.

Credentials are read from environment variables. Tests that require missing
credentials are skipped automatically.
"""
import os
from pathlib import Path
from typing import Optional

import pytest

from ksef.constants import Environment

KSEF_NIP = os.environ.get("KSEF_NIP")
KSEF_TOKEN = os.environ.get("KSEF_TOKEN")
KSEF_CERT_PATH = os.environ.get("KSEF_CERT_PATH")
KSEF_KEY_PATH = os.environ.get("KSEF_KEY_PATH")
KSEF_KEY_PASSWORD = os.environ.get("KSEF_KEY_PASSWORD")


@pytest.fixture()
def nip() -> str:
    """NIP from the KSEF_NIP env var. Skips the test if not set."""
    if not KSEF_NIP:
        pytest.skip("KSEF_NIP environment variable not set")
    return KSEF_NIP


@pytest.fixture()
def ksef_token() -> str:
    """KSeF token from the KSEF_TOKEN env var. Skips the test if not set."""
    if not KSEF_TOKEN:
        pytest.skip("KSEF_TOKEN environment variable not set")
    return KSEF_TOKEN


@pytest.fixture()
def signing_cert() -> bytes:
    """PEM certificate bytes from the KSEF_CERT_PATH env var. Skips if not set."""
    if not KSEF_CERT_PATH:
        pytest.skip("KSEF_CERT_PATH environment variable not set")
    path = Path(KSEF_CERT_PATH)
    if not path.exists():
        pytest.skip(f"Certificate file not found: {KSEF_CERT_PATH}")
    return path.read_bytes()


@pytest.fixture()
def private_key() -> bytes:
    """PEM private key bytes from the KSEF_KEY_PATH env var. Skips if not set."""
    if not KSEF_KEY_PATH:
        pytest.skip("KSEF_KEY_PATH environment variable not set")
    path = Path(KSEF_KEY_PATH)
    if not path.exists():
        pytest.skip(f"Private key file not found: {KSEF_KEY_PATH}")
    return path.read_bytes()


@pytest.fixture()
def key_password() -> Optional[bytes]:
    """Key password from the KSEF_KEY_PASSWORD env var, or None if unset."""
    if KSEF_KEY_PASSWORD:
        return KSEF_KEY_PASSWORD.encode()
    return None


@pytest.fixture()
def environment() -> Environment:
    """Return the KSEF test environment."""
    return Environment.TEST


@pytest.fixture()
def token_authorization(
    ksef_token: str, environment: Environment
) -> "ksef.auth.token.TokenAuthorization":  # type: ignore[name-defined]  # noqa: F821
    """TokenAuthorization instance (not yet authorized)."""
    from ksef.auth.token import TokenAuthorization

    return TokenAuthorization(token=ksef_token, environment=environment)


@pytest.fixture()
def xades_authorization(
    signing_cert: bytes,
    private_key: bytes,
    key_password: Optional[bytes],
    environment: Environment,
) -> "ksef.auth.xades.XadesAuthorization":  # type: ignore[name-defined]  # noqa: F821
    """XadesAuthorization instance (not yet authorized)."""
    from ksef.auth.xades import XadesAuthorization

    return XadesAuthorization(
        signing_cert=signing_cert,
        private_key=private_key,
        key_password=key_password,
        environment=environment,
    )


@pytest.fixture()
def client_from_token(
    token_authorization: "ksef.auth.token.TokenAuthorization",  # type: ignore[name-defined]  # noqa: F821
    nip: str,
    environment: Environment,
) -> "ksef.client.Client":  # type: ignore[name-defined]  # noqa: F821
    """Fully authorized Client using token auth."""
    from ksef.client import Client

    token_authorization.authorize(nip=nip)
    return Client(authorization=token_authorization, environment=environment)
