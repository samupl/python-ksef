"""Simple token-based authorization implementation."""
import base64
import copy
from datetime import datetime, timezone
from typing import Mapping, cast
from urllib.parse import urljoin

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from requests import Request

from ksef.auth.base import Authorization
from ksef.auth.init_session_token_request import InitSessionTokenRequestBuilder
from ksef.constants import (
    BASE_URL,
    DEFAULT_HEADERS,
    TIMEOUT,
    URL_AUTH_CHALLENGE,
    URL_AUTH_INIT_TOKEN,
)
from ksef.models.responses.authorization_challenge import AuthorizationChallenge
from ksef.models.responses.authorization_token import AuthorizationToken
from ksef.utils import response_to_exception


class TokenAuthorization(Authorization):
    """Simple token-based authorization."""

    authorization_token: AuthorizationToken

    def __init__(
        self, token: str, public_key: str, base_url: str = BASE_URL, timeout: int = TIMEOUT
    ):
        self.base_url = base_url
        self.public_key = public_key
        self.token = token
        self.timeout = timeout

    def modify_request(self, request: Request) -> Request:
        """Enrich requests with authorization headers.

        :param request: Request to be enriched
        """
        request.prepare()
        request.headers["SessionToken"] = self.token
        headers = self.build_headers()
        request.headers.update(headers)
        return request

    def authorize(self, nip: str) -> None:
        """Authorize the token authorization by obtaining a session token."""
        challenge = self.get_authorization_challenge(nip=nip)
        authorization_token = self.init_token(authorization_challenge=challenge, nip=nip)
        self.authorization_token = authorization_token
        self.token = authorization_token.session_token.token

    def build_url(self, url: str) -> str:
        """Construct a full URL."""
        return urljoin(base=self.base_url, url=url)

    @staticmethod
    def build_headers(**optional: str) -> Mapping[str, str]:
        """Construct headers.

        Extends base headers (defined in constants) with options passed
        to this method, otherwise just returns default headers.
        """
        headers = copy.deepcopy(DEFAULT_HEADERS)
        headers.update(optional)
        return headers

    def get_authorization_challenge(self, nip: str) -> AuthorizationChallenge:
        """Get the token flow authorization challenge."""
        response = requests.post(
            url=self.build_url(URL_AUTH_CHALLENGE),
            headers=self.build_headers(),
            json={
                "contextIdentifier": {
                    "type": "onip",
                    "identifier": nip,
                }
            },
            timeout=TIMEOUT,
        )
        challenge = response.json()
        error = response_to_exception(response)
        if error is not None:
            raise error
        return AuthorizationChallenge(
            timestamp=challenge["timestamp"], challenge=challenge["challenge"]
        )

    def _encrypt_token(self, authorization_challenge: AuthorizationChallenge) -> str:
        public_key = serialization.load_pem_public_key(self.public_key.encode())
        public_key = cast(rsa.RSAPublicKey, public_key)

        timestamp = (
            int(
                datetime.strptime(authorization_challenge.timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
            * 1000
        )
        message = self.token.encode() + b"|" + str(timestamp).encode()
        encrypted_message = public_key.encrypt(plaintext=message, padding=padding.PKCS1v15())
        return base64.b64encode(encrypted_message).decode("utf-8")

    def _build_init_token_xml(
        self, nip: str, authorization_challenge: AuthorizationChallenge
    ) -> str:
        encrypted_token = self._encrypt_token(authorization_challenge=authorization_challenge)

        request_builder = InitSessionTokenRequestBuilder(
            authorization_challenge=authorization_challenge,
            nip=nip,
            encrypted_token=encrypted_token,
        )
        return request_builder.build_xml()

    def init_token(
        self, authorization_challenge: AuthorizationChallenge, nip: str
    ) -> AuthorizationToken:
        """Initialize the session."""
        document_xml = self._build_init_token_xml(
            nip=nip, authorization_challenge=authorization_challenge
        )
        response = requests.post(
            url=self.build_url(URL_AUTH_INIT_TOKEN),
            data=document_xml,
            timeout=self.timeout,
        )
        error = response_to_exception(response)
        if error is not None:
            raise error
        return AuthorizationToken.from_dict(response.json())
