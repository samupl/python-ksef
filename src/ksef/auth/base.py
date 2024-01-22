"""Base authorization class, used to define the API for all implementations."""
from abc import ABC, abstractmethod

from requests import Request


class Authorization(ABC):
    """Base requests-based authorization class."""

    @abstractmethod
    def modify_request(self, request: Request) -> Request:
        """Enrich a prepared request with authorization headers/params, depending on the actual implementation.

        :param request: Request to be enriched
        """
        ...

    @abstractmethod
    def authorize(self, nip: str) -> None:
        """Perform the authorization process."""
        ...
