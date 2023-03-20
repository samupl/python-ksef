"""Simple token-based authorization implementation."""
from requests import Request

from ksef.auth.base import Authorization


class TokenAuthorization(Authorization):
    """Simple token-based authorization."""

    def __init__(self, token: str):
        self.token = token

    def modify_request(self, request: Request) -> Request:
        """Enrich requests with authorization headers.

        :param request: Request to be enriched
        """
        request.prepare()
        request.headers["Authorization"] = self.token  # TODO: This is just a stub implementaion
        return request
