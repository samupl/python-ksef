"""Models for KSEF API v2 authentication responses."""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TokenInfo:  # noqa: D101
    token: str
    valid_until: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenInfo":  # noqa: D102
        return cls(
            token=data["token"],
            valid_until=data.get("validUntil"),
        )


@dataclass
class AuthChallenge:
    """Challenge response from POST /auth/challenge."""

    challenge: str
    timestamp_ms: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthChallenge":  # noqa: D102
        return cls(
            challenge=data["challenge"],
            timestamp_ms=data["timestampMs"],
        )


@dataclass
class SignatureResponse:
    """Response from POST /auth/ksef-token or POST /auth/xades-signature."""

    reference_number: str
    authentication_token: TokenInfo

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignatureResponse":  # noqa: D102
        return cls(
            reference_number=data["referenceNumber"],
            authentication_token=TokenInfo.from_dict(data["authenticationToken"]),
        )


@dataclass
class StatusInfo:  # noqa: D101
    code: int
    description: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusInfo":  # noqa: D102
        return cls(
            code=data["code"],
            description=data["description"],
        )


@dataclass
class AuthStatus:
    """Response from GET /auth/{referenceNumber}."""

    status: StatusInfo
    is_token_redeemed: bool = False
    authentication_date: Optional[str] = None
    token_expiration_date: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthStatus":  # noqa: D102
        return cls(
            status=StatusInfo.from_dict(data["status"]),
            is_token_redeemed=data.get("isTokenRedeemed", False),
            authentication_date=data.get("authenticationDate"),
            token_expiration_date=data.get("tokenExpirationDate"),
        )


@dataclass
class AuthTokens:
    """Response from POST /auth/token/redeem."""

    access_token: TokenInfo
    refresh_token: TokenInfo

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthTokens":  # noqa: D102
        return cls(
            access_token=TokenInfo.from_dict(data["accessToken"]),
            refresh_token=TokenInfo.from_dict(data["refreshToken"]),
        )
