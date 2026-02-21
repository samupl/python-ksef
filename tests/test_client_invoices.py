"""Tests for Client invoice operations."""
import base64
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.x509.oid import NameOID
from responses import RequestsMock

from ksef.auth.base import Authorization
from ksef.client import AES_KEY_SIZE, IV_SIZE, Client, SessionContext
from ksef.constants import (
    URL_INVOICES_GET,
    URL_PUBLIC_KEY_CERTS,
    URL_SESSIONS_INVOICES,
    URL_SESSIONS_INVOICES_STATUS,
    URL_SESSIONS_ONLINE,
    URL_SESSIONS_ONLINE_CLOSE,
    URL_SESSIONS_ONLINE_INVOICES,
    URL_SESSIONS_STATUS,
    Environment,
)
from ksef.models.invoice import (
    Address,
    Invoice,
    InvoiceData,
    InvoiceType,
    Issuer,
    IssuerIdentificationData,
    Subject,
    SubjectIdentificationData,
)
from ksef.models.invoice_annotations import (
    FreeFromVat,
    IntraCommunitySupplyOfNewTransportMethods,
    InvoiceAnnotations,
    MarginProcedure,
    ReverseCharge,
    SelfInvoicing,
    SimplifiedProcedureBySecondTaxPayer,
    SplitPayment,
    TaxSettlementOnPayment,
)
from ksef.models.invoice_rows import InvoiceRow, InvoiceRows
from ksef.models.responses.session import (
    CloseSessionResponse,
    SendInvoiceResponse,
    SessionInvoiceStatusResponse,
    SessionStatusResponse,
)

BASE = Environment.TEST.value


def _generate_test_certificate() -> tuple[bytes, bytes]:
    """Generate a test RSA key pair and self-signed certificate.

    Returns tuple of (certificate_der, private_key_pem).
    """
    private_key = generate_private_key(public_exponent=65537, key_size=2048)

    # Create self-signed certificate
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Test Certificate"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(tz=timezone.utc))
        .not_valid_after(datetime(2030, 1, 1, tzinfo=timezone.utc))
        .sign(private_key, hashes.SHA256())
    )

    cert_der = cert.public_bytes(serialization.Encoding.DER)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return cert_der, private_key_pem


def _create_test_invoice() -> Invoice:
    """Create a test invoice for use in tests."""
    return Invoice(
        issuer=Issuer(
            identification_data=IssuerIdentificationData(
                nip="1111111111", full_name="Test Company Sp. z o.o."
            ),
            email="test@example.com",
            phone="+48 123456789",
            address=Address(
                country_code="PL",
                city="Warszawa",
                street="Testowa",
                house_number="1",
                apartment_number="2",
                postal_code="00-001",
            ),
        ),
        recipient=Subject(
            identification_data=SubjectIdentificationData(nip="2222222222"),
        ),
        invoice_data=InvoiceData(
            currency_code="PLN",
            issue_date=date(2024, 1, 15),
            issue_number="TEST/1/2024",
            sell_date=date(2024, 1, 1),
            total_amount=Decimal("100.00"),
            invoice_annotations=InvoiceAnnotations(
                tax_settlement_on_payment=TaxSettlementOnPayment.REGULAR,
                self_invoice=SelfInvoicing.NO,
                reverse_charge=ReverseCharge.NO,
                split_payment=SplitPayment.NO,
                free_from_vat=FreeFromVat.NO,
                intra_community_supply_of_new_transport_methods=IntraCommunitySupplyOfNewTransportMethods.NO,
                simplified_procedure_by_second_tax_payer=SimplifiedProcedureBySecondTaxPayer.NO,
                margin_procedure=MarginProcedure.NO,
            ),
            invoice_type=InvoiceType.REGULAR_VAT,
            invoice_rows=InvoiceRows(rows=[InvoiceRow(name="Test service", tax=23)]),
        ),
        creation_datetime=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
    )


def _create_mock_authorization() -> Authorization:
    """Create a mock authorization that returns a test access token."""
    auth = MagicMock(spec=Authorization)
    auth.get_access_token.return_value = "test-access-token"
    return auth


def _mock_public_key_certs(mocked_responses: RequestsMock, cert_der: bytes) -> None:
    """Add mock response for public key certificates endpoint."""
    cert_b64 = base64.b64encode(cert_der).decode("ascii")
    mocked_responses.add(
        url=f"{BASE}{URL_PUBLIC_KEY_CERTS}",
        method="GET",
        content_type="application/json",
        json=[
            {
                "certificate": cert_b64,
                "usage": ["SymmetricKeyEncryption"],
            }
        ],
    )


def test_open_session(mocked_responses: RequestsMock) -> None:
    """Test opening an online session."""
    cert_der, _ = _generate_test_certificate()

    # Mock the public key certificates endpoint
    _mock_public_key_certs(mocked_responses, cert_der)

    # Mock the open session endpoint
    mocked_responses.add(
        url=f"{BASE}{URL_SESSIONS_ONLINE}",
        method="POST",
        content_type="application/json",
        json={
            "referenceNumber": "session-ref-123",
        },
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    session_context = client.open_session(nip="1234567890")

    assert isinstance(session_context, SessionContext)
    assert session_context.reference_number == "session-ref-123"
    assert len(session_context.aes_key) == AES_KEY_SIZE
    assert len(session_context.iv) == IV_SIZE


def test_send_invoice_in_session(mocked_responses: RequestsMock) -> None:
    """Test sending an invoice within a session."""
    # Create a session context with known AES key and IV
    session_context = SessionContext(
        reference_number="session-ref-123",
        aes_key=b"\x00" * 32,  # 256 bits
        iv=b"\x00" * 16,  # 128 bits
    )

    url = URL_SESSIONS_ONLINE_INVOICES.format(reference_number=session_context.reference_number)
    mocked_responses.add(
        url=f"{BASE}{url}",
        method="POST",
        status=202,
        content_type="application/json",
        json={
            "referenceNumber": "invoice-ref-456",
        },
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    invoice = _create_test_invoice()

    response = client.send_invoice_in_session(
        session_context=session_context,
        invoice=invoice,
    )

    assert isinstance(response, SendInvoiceResponse)
    assert response.reference_number == "invoice-ref-456"
    # Other fields are optional and may not be present in the initial 202 response
    assert response.element_reference_number is None
    assert response.processing_code is None


def test_close_session(mocked_responses: RequestsMock) -> None:
    """Test closing an online session."""
    session_context = SessionContext(
        reference_number="session-ref-123",
        aes_key=b"\x00" * 32,
        iv=b"\x00" * 16,
    )

    url = URL_SESSIONS_ONLINE_CLOSE.format(reference_number=session_context.reference_number)
    mocked_responses.add(
        url=f"{BASE}{url}",
        method="POST",
        content_type="application/json",
        json={
            "referenceNumber": "session-ref-123",
        },
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    response = client.close_session(session_context=session_context)

    assert isinstance(response, CloseSessionResponse)
    assert response.reference_number == "session-ref-123"


def test_close_session_204_no_content(mocked_responses: RequestsMock) -> None:
    """Test closing a session when API returns 204 No Content."""
    session_context = SessionContext(
        reference_number="session-ref-123",
        aes_key=b"\x00" * 32,
        iv=b"\x00" * 16,
    )

    url = URL_SESSIONS_ONLINE_CLOSE.format(reference_number=session_context.reference_number)
    mocked_responses.add(
        url=f"{BASE}{url}",
        method="POST",
        status=204,
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    response = client.close_session(session_context=session_context)

    assert isinstance(response, CloseSessionResponse)
    assert response.reference_number == "session-ref-123"


def test_send_invoice_full_flow(mocked_responses: RequestsMock) -> None:
    """Test the full send_invoice() flow: open -> send -> close."""
    cert_der, _ = _generate_test_certificate()

    # Mock public key certificates
    _mock_public_key_certs(mocked_responses, cert_der)

    # Mock open session
    mocked_responses.add(
        url=f"{BASE}{URL_SESSIONS_ONLINE}",
        method="POST",
        content_type="application/json",
        json={
            "referenceNumber": "session-ref-123",
        },
    )

    # Mock send invoice - URL contains reference number
    mocked_responses.add(
        url=f"{BASE}sessions/online/session-ref-123/invoices",
        method="POST",
        status=202,
        content_type="application/json",
        json={
            "referenceNumber": "invoice-ref-456",
        },
    )

    # Mock close session (204 No Content)
    mocked_responses.add(
        url=f"{BASE}sessions/online/session-ref-123/close",
        method="POST",
        status=204,
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    invoice = _create_test_invoice()

    response = client.send_invoice(nip="1234567890", invoice=invoice)

    assert isinstance(response, SendInvoiceResponse)
    assert response.reference_number == "invoice-ref-456"
    # ksef_reference_number is not returned in the initial 202 response
    assert response.ksef_reference_number is None

    # Verify all four endpoints were called (public key certs + open + send + close)
    assert len(mocked_responses.calls) == 4  # noqa: PLR2004


def test_send_invoice_sets_session_reference_number(mocked_responses: RequestsMock) -> None:
    """Test that send_invoice_in_session sets session_reference_number."""
    session_context = SessionContext(
        reference_number="session-ref-123",
        aes_key=b"\x00" * 32,
        iv=b"\x00" * 16,
    )

    url = URL_SESSIONS_ONLINE_INVOICES.format(reference_number=session_context.reference_number)
    mocked_responses.add(
        url=f"{BASE}{url}",
        method="POST",
        status=202,
        content_type="application/json",
        json={"referenceNumber": "invoice-ref-456"},
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    invoice = _create_test_invoice()

    response = client.send_invoice_in_session(session_context=session_context, invoice=invoice)

    assert response.session_reference_number == "session-ref-123"


def test_get_session_status(mocked_responses: RequestsMock) -> None:
    """Test getting session status."""
    session_ref = "session-ref-123"
    url = URL_SESSIONS_STATUS.format(reference_number=session_ref)
    mocked_responses.add(
        url=f"{BASE}{url}",
        method="GET",
        content_type="application/json",
        json={
            "status": {"code": 200, "description": "Completed"},
            "invoiceCount": 5,
            "successfulInvoiceCount": 4,
            "failedInvoiceCount": 1,
        },
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    response = client.get_session_status(session_reference_number=session_ref)

    assert isinstance(response, SessionStatusResponse)
    assert response.status.code == 200  # noqa: PLR2004
    assert response.status.description == "Completed"
    assert response.invoice_count == 5  # noqa: PLR2004
    assert response.successful_invoice_count == 4  # noqa: PLR2004
    assert response.failed_invoice_count == 1


def test_get_invoice_status(mocked_responses: RequestsMock) -> None:
    """Test getting a specific invoice status."""
    session_ref = "session-ref-123"
    invoice_ref = "invoice-ref-456"
    url = URL_SESSIONS_INVOICES_STATUS.format(
        reference_number=session_ref, invoice_reference_number=invoice_ref
    )
    mocked_responses.add(
        url=f"{BASE}{url}",
        method="GET",
        content_type="application/json",
        json={
            "ordinalNumber": 1,
            "referenceNumber": invoice_ref,
            "status": {
                "code": 400,
                "description": "Validation failed",
                "details": ["Invalid NIP", "Missing field: issueDate"],
            },
            "invoiceNumber": "FV/2024/001",
            "ksefNumber": "KSEF-2024-001",
            "invoicingDate": "2024-01-15",
        },
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    response = client.get_invoice_status(
        session_reference_number=session_ref, invoice_reference_number=invoice_ref
    )

    assert isinstance(response, SessionInvoiceStatusResponse)
    assert response.ordinal_number == 1
    assert response.reference_number == invoice_ref
    assert response.status.code == 400  # noqa: PLR2004
    assert response.status.description == "Validation failed"
    assert response.status.details == ["Invalid NIP", "Missing field: issueDate"]
    assert response.invoice_number == "FV/2024/001"
    assert response.ksef_number == "KSEF-2024-001"
    assert response.invoicing_date == "2024-01-15"


def test_get_session_invoices(mocked_responses: RequestsMock) -> None:
    """Test getting all invoice statuses for a session."""
    session_ref = "session-ref-123"
    url = URL_SESSIONS_INVOICES.format(reference_number=session_ref)
    mocked_responses.add(
        url=f"{BASE}{url}?PageSize=10",
        method="GET",
        content_type="application/json",
        json=[
            {
                "ordinalNumber": 1,
                "referenceNumber": "invoice-ref-001",
                "status": {"code": 200, "description": "Accepted"},
                "ksefNumber": "KSEF-2024-001",
            },
            {
                "ordinalNumber": 2,
                "referenceNumber": "invoice-ref-002",
                "status": {"code": 200, "description": "Accepted"},
            },
        ],
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    invoices = client.get_session_invoices(session_reference_number=session_ref)

    assert len(invoices) == 2  # noqa: PLR2004
    assert all(isinstance(inv, SessionInvoiceStatusResponse) for inv in invoices)
    assert invoices[0].reference_number == "invoice-ref-001"
    assert invoices[0].status.code == 200  # noqa: PLR2004
    assert invoices[0].ksef_number == "KSEF-2024-001"
    assert invoices[1].reference_number == "invoice-ref-002"
    assert invoices[1].ksef_number is None


def test_download_invoice(mocked_responses: RequestsMock) -> None:
    """Test downloading an invoice by KSEF reference number."""
    ksef_ref = "KSEF-2024-001"
    invoice_xml = b"<?xml version='1.0'?><Faktura><Test>content</Test></Faktura>"

    mocked_responses.add(
        url=f"{BASE}{URL_INVOICES_GET.format(ksef_reference_number=ksef_ref)}",
        method="GET",
        content_type="application/xml",
        body=invoice_xml,
    )

    auth = _create_mock_authorization()
    client = Client(authorization=auth, environment=Environment.TEST)
    result = client.download_invoice(ksef_reference_number=ksef_ref)

    assert result == invoice_xml
