"""Test suite for XML converters."""
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from bs4 import BeautifulSoup

from ksef.models.invoice import (
    PAYMENT_METHOD_BANK_TRANSFER,
    PAYMENT_METHOD_CARD,
    PAYMENT_METHOD_CASH,
    Address,
    EuVatIdentification,
    ForeignIdentification,
    Invoice,
    InvoiceData,
    InvoiceType,
    Issuer,
    IssuerIdentificationData,
    NipIdentification,
    NoIdentification,
    PaymentInfo,
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
        creation_datetime=datetime(2024, 1, 22, 10, 30, 0, tzinfo=timezone.utc),
    )
    actual_content = convert_invoice_to_xml(invoice)
    assert_xml_equal(actual_content=actual_content, expected_content=expected_content)


def test_without_apartment_number() -> None:
    """Test that NrLokalu element is omitted when apartment_number is None."""
    with (RESOURCES_DIR / "invoice_without_apartment.xml").open("rb") as fd:
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
                apartment_number=None,
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
        creation_datetime=datetime(2024, 1, 22, 10, 30, 0, tzinfo=timezone.utc),
    )
    actual_content = convert_invoice_to_xml(invoice)
    assert_xml_equal(actual_content=actual_content, expected_content=expected_content)
    assert b"NrLokalu" not in actual_content


def _make_invoice(recipient: Subject) -> Invoice:
    """Build a minimal invoice with the given recipient."""
    return Invoice(
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
        recipient=recipient,
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
        creation_datetime=datetime(2024, 1, 22, 10, 30, 0, tzinfo=timezone.utc),
    )


def test_recipient_eu_vat() -> None:
    """Test EU company recipient produces KodUE + NrVatUE elements."""
    invoice = _make_invoice(
        Subject(
            identification_data=EuVatIdentification(eu_country_code="DE", eu_vat_number="123456789")
        )
    )
    xml = convert_invoice_to_xml(invoice)
    soup = BeautifulSoup(xml, "xml")
    id_data = soup.find("Podmiot2").find("DaneIdentyfikacyjne")
    assert id_data.find("KodUE").text == "DE"
    assert id_data.find("NrVatUE").text == "123456789"
    assert id_data.find("NIP") is None


def test_recipient_foreign_id() -> None:
    """Test non-EU recipient with country code produces KodKraju + NrID."""
    invoice = _make_invoice(
        Subject(identification_data=ForeignIdentification(country_code="US", tax_id="EIN123"))
    )
    xml = convert_invoice_to_xml(invoice)
    soup = BeautifulSoup(xml, "xml")
    id_data = soup.find("Podmiot2").find("DaneIdentyfikacyjne")
    assert id_data.find("KodKraju").text == "US"
    assert id_data.find("NrID").text == "EIN123"
    assert id_data.find("NIP") is None


def test_recipient_foreign_id_without_country() -> None:
    """Test non-EU recipient without country code produces only NrID."""
    invoice = _make_invoice(Subject(identification_data=ForeignIdentification(tax_id="XYZ999")))
    xml = convert_invoice_to_xml(invoice)
    soup = BeautifulSoup(xml, "xml")
    id_data = soup.find("Podmiot2").find("DaneIdentyfikacyjne")
    assert id_data.find("NrID").text == "XYZ999"
    assert id_data.find("KodKraju") is None


def test_recipient_no_id() -> None:
    """Test individual/B2C recipient produces BrakID and supports Nazwa."""
    invoice = _make_invoice(Subject(identification_data=NoIdentification(), name="Jan Kowalski"))
    xml = convert_invoice_to_xml(invoice)
    soup = BeautifulSoup(xml, "xml")
    podmiot2 = soup.find("Podmiot2")
    id_data = podmiot2.find("DaneIdentyfikacyjne")
    assert id_data.find("BrakID").text == "1"
    assert id_data.find("NIP") is None
    assert podmiot2.find("Nazwa").text == "Jan Kowalski"


def test_recipient_with_name() -> None:
    """Test NIP recipient with name produces both NIP and Nazwa."""
    invoice = _make_invoice(
        Subject(
            identification_data=NipIdentification(nip="2222222222"),
            name="Firma Testowa Sp. z o.o.",
        )
    )
    xml = convert_invoice_to_xml(invoice)
    soup = BeautifulSoup(xml, "xml")
    podmiot2 = soup.find("Podmiot2")
    assert podmiot2.find("DaneIdentyfikacyjne").find("NIP").text == "2222222222"
    assert podmiot2.find("Nazwa").text == "Firma Testowa Sp. z o.o."


def _make_invoice_with_payment(payment_info: PaymentInfo) -> Invoice:
    """Build a minimal invoice with the given payment info."""
    invoice = _make_invoice(Subject(identification_data=NipIdentification(nip="2222222222")))
    invoice.invoice_data.payment_info = payment_info
    return invoice


def test_payment_info_omitted() -> None:
    """Platnosc element is not emitted when payment_info is None."""
    invoice = _make_invoice(Subject(identification_data=NipIdentification(nip="2222222222")))
    xml = convert_invoice_to_xml(invoice)
    soup = BeautifulSoup(xml, "xml")
    assert soup.find("Platnosc") is None


def test_payment_info_bank_transfer_with_due_date() -> None:
    """Bank transfer invoice emits FormaPlatnosci=6, Termin and RachunekBankowy."""
    invoice = _make_invoice_with_payment(
        PaymentInfo(
            due_date=date(2024, 2, 5),
            method=PAYMENT_METHOD_BANK_TRANSFER,
            bank_account_number="12345678901234567890123456",
        )
    )
    soup = BeautifulSoup(convert_invoice_to_xml(invoice), "xml")
    platnosc = soup.find("Platnosc")
    assert platnosc is not None
    assert platnosc.find("Zaplacono") is None
    assert platnosc.find("DataZaplaty") is None
    assert platnosc.find("TerminPlatnosci").find("Termin").text == "2024-02-05"
    assert platnosc.find("FormaPlatnosci").text == "6"
    assert platnosc.find("RachunekBankowy").find("NrRB").text == "12345678901234567890123456"


def test_payment_info_paid_in_full() -> None:
    """Already-paid invoice emits Zaplacono=1 and DataZaplaty."""
    invoice = _make_invoice_with_payment(
        PaymentInfo(
            is_paid=True,
            payment_date=date(2024, 1, 22),
            method=PAYMENT_METHOD_CASH,
        )
    )
    soup = BeautifulSoup(convert_invoice_to_xml(invoice), "xml")
    platnosc = soup.find("Platnosc")
    assert platnosc.find("Zaplacono").text == "1"
    assert platnosc.find("DataZaplaty").text == "2024-01-22"
    assert platnosc.find("FormaPlatnosci").text == "1"
    assert platnosc.find("RachunekBankowy") is None


def test_payment_info_with_due_description() -> None:
    """Due date with custom description emits both Termin and TerminOpis."""
    invoice = _make_invoice_with_payment(
        PaymentInfo(
            due_date=date(2024, 3, 1),
            due_description="14 dni od otrzymania faktury",
            method=PAYMENT_METHOD_CARD,
        )
    )
    soup = BeautifulSoup(convert_invoice_to_xml(invoice), "xml")
    termin_platnosci = soup.find("Platnosc").find("TerminPlatnosci")
    assert termin_platnosci.find("Termin").text == "2024-03-01"
    assert termin_platnosci.find("TerminOpis").text == "14 dni od otrzymania faktury"
    assert soup.find("FormaPlatnosci").text == "2"


def test_payment_info_is_paid_false_omits_zaplacono() -> None:
    """Zaplacono element is not emitted when is_paid is False (default)."""
    invoice = _make_invoice_with_payment(PaymentInfo(method=PAYMENT_METHOD_BANK_TRANSFER))
    soup = BeautifulSoup(convert_invoice_to_xml(invoice), "xml")
    platnosc = soup.find("Platnosc")
    assert platnosc is not None
    assert platnosc.find("Zaplacono") is None
