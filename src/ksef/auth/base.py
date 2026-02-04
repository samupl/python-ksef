"""Base authorization class, used to define the API for all implementations."""
from abc import ABC, abstractmethod

from ksef.models.responses.auth import AuthTokens


class Authorization(ABC):
    """Base authorization class for KSEF API v2."""

    _tokens: AuthTokens

    @abstractmethod
    def authorize(self, nip: str) -> AuthTokens:
        """Perform the full authorization flow and return access/refresh tokens.

        Parameters
        ----------
        nip : str
            The NIP (tax identification number) to authorize with.
        """
        ...

    def get_access_token(self) -> str:
        """Return the current access token for API calls."""
        return self._tokens.access_token.token
