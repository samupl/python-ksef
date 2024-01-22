"""KSEF-specific exceptions."""
from requests import Response


class KsefError(Exception):
    """Base exception class for all KSEF-related exceptions."""

    @property
    def prefix(self) -> str:
        """
        Pretty auto-generated error message prefix.

        Used for transforming the exception to a human-readable error message.
        """
        from ksef.utils import camelcase_to_words

        prefix = self.__class__.__name__
        return camelcase_to_words(prefix)

    @property
    def message(self) -> str:
        """Human-readable error message."""
        return "-this exception has no message-"

    @property
    def should_retry(self) -> bool:
        """Whether the call that called the exception can be retried."""
        return False

    def __str__(self) -> str:  # noqa: D105
        return f"{self.prefix}: {self.message}"


class _ResponseMixin:
    def __init__(self, response: Response):
        self.response = response
        super().__init__()


class UnsupportedResponseError(_ResponseMixin, KsefError):
    """Unsupported response status code."""

    @property
    def message(self) -> str:
        """Human-readable error message."""
        return f"Unsupported response status code: {self.response.status_code}"


class RateLimitExceededError(_ResponseMixin, KsefError):
    """Rate limit exceeded."""

    should_retry = True
    message = (
        "Your client has sent too many requests and has been throttled. Please try again later."
    )
