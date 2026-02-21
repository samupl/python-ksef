"""Models for KSEF API v2 session responses."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class EncryptionKeyInfo:
    """Encryption key information from session response."""

    algorithm: str
    public_key: str  # Base64-encoded DER public key

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EncryptionKeyInfo":
        """Create EncryptionKeyInfo from API response dictionary."""
        return cls(
            algorithm=data["algorithm"],
            public_key=data["publicKey"],
        )


@dataclass
class SessionTokenInfo:
    """Session token information."""

    token: str
    valid_until: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionTokenInfo":
        """Create SessionTokenInfo from API response dictionary."""
        return cls(
            token=data["token"],
            valid_until=data.get("validUntil"),
        )


@dataclass
class OpenSessionResponse:
    """Response from POST /sessions/online."""

    reference_number: str
    session_token: SessionTokenInfo
    encryption_key: EncryptionKeyInfo

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OpenSessionResponse":
        """Create OpenSessionResponse from API response dictionary."""
        return cls(
            reference_number=data["referenceNumber"],
            session_token=SessionTokenInfo.from_dict(data["sessionToken"]),
            encryption_key=EncryptionKeyInfo.from_dict(data["encryptionKey"]),
        )


@dataclass
class RawResponse:
    """Raw HTTP response data for audit purposes."""

    status_code: int
    headers: Dict[str, str]
    body: Dict[str, Any]


@dataclass
class SendInvoiceResponse:
    """Response from POST /sessions/online/invoices.

    Note: Initially the API returns only the reference_number (202 Accepted).
    Other fields may be populated when querying invoice status later.
    """

    reference_number: str
    element_reference_number: Optional[str] = None
    processing_code: Optional[int] = None
    processing_description: Optional[str] = None
    ksef_reference_number: Optional[str] = None
    session_reference_number: Optional[str] = None
    invoice_xml: Optional[bytes] = None
    raw_response: Optional[RawResponse] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SendInvoiceResponse":
        """Create SendInvoiceResponse from API response dictionary."""
        return cls(
            reference_number=data["referenceNumber"],
            element_reference_number=data.get("elementReferenceNumber"),
            processing_code=data.get("processingCode"),
            processing_description=data.get("processingDescription"),
            ksef_reference_number=data.get("ksefReferenceNumber"),
        )


@dataclass
class CloseSessionResponse:
    """Response from POST /sessions/online/close."""

    reference_number: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CloseSessionResponse":
        """Create CloseSessionResponse from API response dictionary."""
        return cls(
            reference_number=data["referenceNumber"],
        )


@dataclass
class InvoiceStatus:
    """Invoice processing status."""

    code: int
    description: str
    details: Optional[List[str]] = None
    extensions: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvoiceStatus":
        """Create InvoiceStatus from API response dictionary."""
        return cls(
            code=data["code"],
            description=data["description"],
            details=data.get("details"),
            extensions=data.get("extensions"),
        )


@dataclass
class SessionInvoiceStatusResponse:
    """Response from GET /sessions/{ref}/invoices/{invoiceRef}."""

    ordinal_number: int
    reference_number: str
    status: InvoiceStatus
    invoice_number: Optional[str] = None
    ksef_number: Optional[str] = None
    invoicing_date: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionInvoiceStatusResponse":
        """Create SessionInvoiceStatusResponse from API response dictionary."""
        return cls(
            ordinal_number=data["ordinalNumber"],
            reference_number=data["referenceNumber"],
            status=InvoiceStatus.from_dict(data["status"]),
            invoice_number=data.get("invoiceNumber"),
            ksef_number=data.get("ksefNumber"),
            invoicing_date=data.get("invoicingDate"),
        )


@dataclass
class SessionStatusResponse:
    """Response from GET /sessions/{ref}."""

    status: InvoiceStatus
    invoice_count: int
    successful_invoice_count: int
    failed_invoice_count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionStatusResponse":
        """Create SessionStatusResponse from API response dictionary."""
        return cls(
            status=InvoiceStatus.from_dict(data["status"]),
            invoice_count=data["invoiceCount"],
            successful_invoice_count=data["successfulInvoiceCount"],
            failed_invoice_count=data["failedInvoiceCount"],
        )
