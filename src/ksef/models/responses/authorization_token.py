"""Models for authorization token response."""
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ContextIdentifier:  # noqa: D101
    type: str  # noqa: A003
    identifier: str

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ContextIdentifier":  # noqa: D102
        return ContextIdentifier(type=data["type"], identifier=data["identifier"])


@dataclass
class ContextName:  # noqa: D101
    full_name: str


@dataclass
class CredentialRole:  # noqa: D101
    type: str  # noqa: A003
    role_type: str
    role_description: str
    start_timestamp: str

    @classmethod
    def from_list(cls, data: List[Dict[str, str]]) -> List["CredentialRole"]:  # noqa: D102
        return [cls.from_dict(cr) for cr in data]

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "CredentialRole":  # noqa: D102
        return cls(
            type=data["type"],
            role_type=data["roleType"],
            role_description=data["roleDescription"],
            start_timestamp=data["startTimestamp"],
        )


@dataclass
class Context:  # noqa: D101
    context_identifier: ContextIdentifier
    context_name: ContextName
    credentials_role_list: List[CredentialRole]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":  # noqa: D102
        return cls(
            context_identifier=ContextIdentifier.from_dict(data["contextIdentifier"]),
            context_name=ContextName(full_name=data["contextName"]["fullName"]),
            credentials_role_list=CredentialRole.from_list(data["credentialsRoleList"]),
        )


@dataclass
class SessionToken:  # noqa: D101
    token: str
    context: Context

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionToken":  # noqa: D102
        return cls(token=data["token"], context=Context.from_dict(data["context"]))


@dataclass
class AuthorizationToken:
    """Session token for authorization."""

    timestamp: str
    reference_number: str
    session_token: SessionToken

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorizationToken":  # noqa: D102
        return cls(
            timestamp=data["timestamp"],
            reference_number=data["referenceNumber"],
            session_token=SessionToken.from_dict(data["sessionToken"]),
        )
