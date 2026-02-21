"""Integration tests for invoice sending operations.

These tests require:
- KSEF_TOKEN: KSeF authorization token
- KSEF_NIP: Tax identification number

Tests are automatically skipped if credentials are not set.
"""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from ksef.client import AES_KEY_SIZE, IV_SIZE, Client, SessionContext
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
)


def _create_test_invoice(nip: str) -> Invoice:
    """Create a test invoice with the given issuer NIP."""
    return Invoice(
        issuer=Issuer(
            identification_data=IssuerIdentificationData(
                nip=nip, full_name="Test Company Sp. z o.o."
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
            identification_data=SubjectIdentificationData(nip=nip),  # Self-invoice for testing
        ),
        invoice_data=InvoiceData(
            currency_code="PLN",
            issue_date=datetime.now(tz=timezone.utc).date(),
            issue_number=f"TEST/{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}/2024",
            sell_date=datetime.now(tz=timezone.utc).date(),
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
            invoice_rows=InvoiceRows(rows=[InvoiceRow(name="Integration test service", tax=23)]),
        ),
        creation_datetime=datetime.now(tz=timezone.utc),
    )


@pytest.mark.integration()
def test_open_session(
    client_from_token: Client,
    nip: str,
) -> None:
    """Test opening an online session."""
    session_context = client_from_token.open_session(nip=nip)

    assert isinstance(session_context, SessionContext)
    assert session_context.reference_number
    assert len(session_context.aes_key) == AES_KEY_SIZE
    assert len(session_context.iv) == IV_SIZE

    # Clean up: close the session
    client_from_token.close_session(session_context)


@pytest.mark.integration()
def test_session_flow_open_send_close(
    client_from_token: Client,
    nip: str,
) -> None:
    """Test the full session flow: open -> send invoice -> close."""
    # Open session
    session_context = client_from_token.open_session(nip=nip)
    assert isinstance(session_context, SessionContext)

    try:
        # Send invoice
        invoice = _create_test_invoice(nip)
        send_response = client_from_token.send_invoice_in_session(
            session_context=session_context,
            invoice=invoice,
        )

        assert isinstance(send_response, SendInvoiceResponse)
        assert send_response.reference_number
        # Note: element_reference_number and ksef_reference_number are not returned
        # in the initial 202 response; they would be available when querying status

    finally:
        # Always close session
        close_response = client_from_token.close_session(session_context)
        assert isinstance(close_response, CloseSessionResponse)
        assert close_response.reference_number


@pytest.mark.integration()
def test_send_invoice_convenience_method(
    client_from_token: Client,
    nip: str,
) -> None:
    """Test the high-level send_invoice() convenience method."""
    invoice = _create_test_invoice(nip)

    response = client_from_token.send_invoice(nip=nip, invoice=invoice)

    assert isinstance(response, SendInvoiceResponse)
    assert response.reference_number
    # Note: element_reference_number is not in the initial 202 response


@pytest.mark.integration()
def test_download_invoice(
    client_from_token: Client,
) -> None:
    """Test downloading an invoice by KSEF reference number.

    Note: This test requires a known KSEF reference number to exist.
    For CI environments, this test may be skipped if no reference is available.
    """
    # This would require a known KSEF reference number
    # For now, we'll skip this test unless we have a reference to use
    pytest.skip("Requires a known KSEF reference number to download")
