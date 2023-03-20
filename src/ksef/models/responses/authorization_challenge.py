"""Model for authorization challenge response."""
from dataclasses import dataclass


@dataclass
class AuthorizationChallenge:
    """Token flow authorization challenge."""

    timestamp: str
    challenge: str
