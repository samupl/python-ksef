"""Test suite for XML converters."""
from datetime import date
from decimal import Decimal
from pathlib import Path

from bs4 import BeautifulSoup

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
from ksef.xml_converters import convert_invoice_to_xml

BASE_DIR = Path(__file__).parent
RESOURCES_DIR = BASE_DIR / "resources"


def assert_xml_equal(actual_content: bytes, expected_content: bytes) -> None:
    """
    Assert if two XML files are the same.

    This method prettifies the XMLs first, because otherwise it would be required to match the XML file byte by byte.
    This way implementation of the XML builder is irrelevant, because the actual parsed content is compared.
    """
    actual = BeautifulSoup(actual_content, "xml").prettify()
    expected = BeautifulSoup(expected_content, "xml").prettify()
    assert actual == expected


def test_simple() -> None:
    """Test if a simple invoice is converted to XML as supposed to."""
    with (RESOURCES_DIR / "invoice.xml").open("rb") as fd:
        expected_content = fd.read()

    invoice = Invoice(
        issuer=Issuer(
            identification_data=IssuerIdentificationData(
                nip="1111111111", full_name="Example Company 1 Sp z o. o."
            ),
            email="example@example.com",
            phone="+48 111111111",
            address=Address(
                country_code="PL",
                city="Warszawa",
                street="Kwiatowa",
                house_number="1",
                apartment_number="2",
                postal_code="00-001",
            ),
        ),
        recipient=Subject(
            identification_data=SubjectIdentificationData(
                nip="2222222222",
            ),
        ),
        invoice_data=InvoiceData(
            currency_code="PLN",
            issue_date=date(2024, 1, 22),
            issue_number="FA/1/2024",
            sell_date=date(2024, 1, 1),
            total_amount=Decimal("450.00"),
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
            invoice_rows=InvoiceRows(
                rows=[
                    InvoiceRow(name="Example service 1", tax=23),
                    InvoiceRow(name="Example service 2", tax=8),
                ]
            ),
        ),
    )
    actual_content = convert_invoice_to_xml(invoice)
    assert_xml_equal(actual_content=actual_content, expected_content=expected_content)
