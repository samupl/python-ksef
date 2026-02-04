"""KSeF Token-based authorization implementation for API v2."""
import base64
import copy
import logging
import time
from typing import Any, Dict, List, Mapping, cast
from urllib.parse import urljoin

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from ksef.auth.base import Authorization
from ksef.constants import (
    DEFAULT_HEADERS,
    TIMEOUT,
    URL_AUTH_CHALLENGE,
    URL_AUTH_KSEF_TOKEN,
    URL_AUTH_STATUS,
    URL_AUTH_TOKEN_REDEEM,
    URL_PUBLIC_KEY_CERTS,
    Environment,
)
from ksef.exceptions import AuthenticationError
from ksef.models.responses.auth import AuthChallenge, AuthStatus, AuthTokens, SignatureResponse
from ksef.utils import response_to_exception

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 1.0
_POLL_MAX_ATTEMPTS = 60


class TokenAuthorization(Authorization):
    """KSeF Token-based authorization for API v2."""

    def __init__(
        self,
        token: str,
        environment: Environment = Environment.PRODUCTION,
        timeout: int = TIMEOUT,
    ):
        self.token = token
        self.environment = environment
        self.base_url = environment.value
        self.timeout = timeout

    def authorize(self, nip: str) -> AuthTokens:
        """Perform the full v2 token authorization flow.

        Parameters
        ----------
        nip : str
            The NIP (tax identification number) to authorize with.
        """
        public_key = self._fetch_encryption_key()
        challenge = self._get_challenge()
        encrypted_token = self._encrypt_token(
            challenge=challenge,
            public_key=public_key,
        )
        signature_response = self._init_ksef_token(
            challenge=challenge,
            nip=nip,
            encrypted_token=encrypted_token,
        )
        self._poll_auth_status(
            reference_number=signature_response.reference_number,
            authentication_token=signature_response.authentication_token.token,
        )
        tokens = self._redeem_token(
            authentication_token=signature_response.authentication_token.token,
        )
        self._tokens = tokens
        return tokens

    def get_access_token(self) -> str:
        """Return the current access token for API calls."""
        return self._tokens.access_token.token

    def build_url(self, url: str) -> str:
        """Construct a full URL."""
        return urljoin(base=self.base_url, url=url)

    @staticmethod
    def build_headers(**optional: str) -> Mapping[str, str]:
        """Construct headers."""
        headers = copy.deepcopy(DEFAULT_HEADERS)
        headers.update(optional)
        return headers

    def _fetch_encryption_key(self) -> rsa.RSAPublicKey:
        """Fetch public key certificates and find the KsefTokenEncryption key."""
        response = requests.get(
            url=self.build_url(URL_PUBLIC_KEY_CERTS),
            headers=self.build_headers(),
            timeout=self.timeout,
        )
        error = response_to_exception(response)
        if error is not None:
            raise error

        certs: List[Dict[str, Any]] = response.json()
        for cert in certs:
            usages = cert.get("usage", [])
            if "KsefTokenEncryption" in usages:
                cert_b64 = cert["certificate"]
                cert_der = base64.b64decode(cert_b64)
                x509_cert = x509.load_der_x509_certificate(cert_der)
                public_key = x509_cert.public_key()
                return cast(rsa.RSAPublicKey, public_key)

        raise AuthenticationError("No KsefTokenEncryption public key found in server response.")

    def _get_challenge(self) -> AuthChallenge:
        """Get the authorization challenge."""
        response = requests.post(
            url=self.build_url(URL_AUTH_CHALLENGE),
            headers=self.build_headers(),
            json={},
            timeout=self.timeout,
        )
        logger.debug(
            "Authorization challenge response (%s): %s", response.status_code, response.text
        )
        error = response_to_exception(response)
        if error is not None:
            raise error
        return AuthChallenge.from_dict(response.json())

    def _encrypt_token(
        self,
        challenge: AuthChallenge,
        public_key: rsa.RSAPublicKey,
    ) -> str:
        """Encrypt the token with RSA-OAEP using the server's public key."""
        timestamp_ms = challenge.timestamp_ms
        message = f"{self.token}|{timestamp_ms}".encode()
        encrypted = public_key.encrypt(
            plaintext=message,
            padding=padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted).decode("utf-8")

    def _init_ksef_token(
        self,
        challenge: AuthChallenge,
        nip: str,
        encrypted_token: str,
    ) -> SignatureResponse:
        """Submit encrypted token to POST /auth/ksef-token."""
        payload = {
            "challenge": challenge.challenge,
            "contextIdentifier": {
                "type": "Nip",
                "value": nip,
            },
            "encryptedToken": encrypted_token,
        }
        response = requests.post(
            url=self.build_url(URL_AUTH_KSEF_TOKEN),
            headers=self.build_headers(),
            json=payload,
            timeout=self.timeout,
        )
        logger.debug("Init ksef-token response (%s): %s", response.status_code, response.text)
        error = response_to_exception(response)
        if error is not None:
            raise error
        return SignatureResponse.from_dict(response.json())

    def _poll_auth_status(
        self,
        reference_number: str,
        authentication_token: str,
    ) -> AuthStatus:
        """Poll GET /auth/{referenceNumber} until authentication completes."""
        url = self.build_url(URL_AUTH_STATUS.format(reference_number=reference_number))
        for attempt in range(_POLL_MAX_ATTEMPTS):
            response = requests.get(
                url=url,
                headers={
                    **self.build_headers(),
                    "Authorization": f"Bearer {authentication_token}",
                },
                timeout=self.timeout,
            )
            error = response_to_exception(response)
            if error is not None:
                raise error

            status = AuthStatus.from_dict(response.json())
            if status.status.code == 200:  # noqa: PLR2004
                return status

            logger.debug(
                "Auth status poll attempt %d: code=%d, desc=%s",
                attempt + 1,
                status.status.code,
                status.status.description,
            )
            time.sleep(_POLL_INTERVAL)

        raise AuthenticationError(
            f"Authentication polling timed out after {_POLL_MAX_ATTEMPTS} attempts."
        )

    def _redeem_token(self, authentication_token: str) -> AuthTokens:
        """Redeem authentication token for access/refresh tokens via POST /auth/token/redeem."""
        response = requests.post(
            url=self.build_url(URL_AUTH_TOKEN_REDEEM),
            headers={
                **self.build_headers(),
                "Authorization": f"Bearer {authentication_token}",
            },
            json={},
            timeout=self.timeout,
        )
        logger.debug("Token redeem response (%s): %s", response.status_code, response.text)
        error = response_to_exception(response)
        if error is not None:
            raise error
        return AuthTokens.from_dict(response.json())
