"""Simple token-based authorization implementation."""
import copy
from typing import Mapping
from urllib.parse import urljoin

import requests
from requests import Request

from ksef.auth.base import Authorization
from ksef.constants import BASE_URL, DEFAULT_HEADERS, TIMEOUT, URL_SESSION_CHALLENGE
from ksef.models.responses.authorization_challenge import AuthorizationChallenge


class TokenAuthorization(Authorization):
    """Simple token-based authorization."""

    def __init__(self, token: str, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = token

    def modify_request(self, request: Request) -> Request:
        """Enrich requests with authorization headers.

        :param request: Request to be enriched
        """
        request.prepare()
        request.headers["Authorization"] = self.token  # TODO: This is just a stub implementaion
        return request

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
            url=self.build_url(URL_SESSION_CHALLENGE),
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
        return AuthorizationChallenge(
            timestamp=challenge["timestamp"], challenge=challenge["challenge"]
        )
