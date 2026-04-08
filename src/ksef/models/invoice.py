"""Invoice model."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Sequence, Union

from pydantic import BaseModel

from ksef.models.invoice_annotations import InvoiceAnnotations
from ksef.models.invoice_rows import InvoiceRows


class TaxSummary(BaseModel):
    """Tax summary totals per rate for the Fa section.

    Each field pair (net + vat) corresponds to a tax rate group.
    All fields are optional — only include those that apply to the invoice.
    """

    # 23% or 22% (standard rate)
    net_standard: Optional[Decimal] = None  # P_13_1
    vat_standard: Optional[Decimal] = None  # P_14_1
    vat_standard_pln: Optional[Decimal] = None  # P_14_1W (foreign currency)

    # 8% or 7% (first reduced rate)
    net_reduced_1: Optional[Decimal] = None  # P_13_2
    vat_reduced_1: Optional[Decimal] = None  # P_14_2
    vat_reduced_1_pln: Optional[Decimal] = None  # P_14_2W

    # 5% (second reduced rate)
    net_reduced_2: Optional[Decimal] = None  # P_13_3
    vat_reduced_2: Optional[Decimal] = None  # P_14_3
    vat_reduced_2_pln: Optional[Decimal] = None  # P_14_3W

    # 4% or 3% (taxi flat-rate)
    net_flat_rate: Optional[Decimal] = None  # P_13_4
    vat_flat_rate: Optional[Decimal] = None  # P_14_4

    # OSS/IOSS procedure tax
    net_oss: Optional[Decimal] = None
    vat_oss: Optional[Decimal] = None

    # 0% rates (no VAT fields — VAT is zero)
    net_zero_domestic: Optional[Decimal] = None
    net_zero_wdt: Optional[Decimal] = None
    net_zero_export: Optional[Decimal] = None

    # Exempt from tax
    net_exempt: Optional[Decimal] = None

    # Not subject to taxation
    net_not_subject: Optional[Decimal] = None  # P_13_8 (np I)
    net_not_subject_art100: Optional[Decimal] = None  # P_13_9 (np II)

    # Reverse charge (oo)
    net_reverse_charge: Optional[Decimal] = None  # P_13_10


class IssuerIdentificationData(BaseModel):
    """
    Subject identification data.

    Corresponds to the field TPodmiot1/TPodmiot2 from the invoice XML schema.
    """

    nip: str
    full_name: str


class NipIdentification(BaseModel):
    """Polish NIP identification for Podmiot2."""

    nip: str


class EuVatIdentification(BaseModel):
    """EU VAT identification for Podmiot2."""

    eu_country_code: str
    eu_vat_number: str


class ForeignIdentification(BaseModel):
    """Non-EU foreign tax identification for Podmiot2."""

    country_code: Optional[str] = None
    tax_id: str


class NoIdentification(BaseModel):
    """No tax identification (individuals, B2C) for Podmiot2."""


# Backwards-compatible alias
SubjectIdentificationData = NipIdentification


class Address(BaseModel):
    """Subject address data.

    Corresponds to the type TAdres from the invoice XML schema.
    """

    country_code: str
    city: str
    street: str
    house_number: str
    apartment_number: Optional[str]
    postal_code: str


class Subject(BaseModel):
    """
    A subject of the invoice (issuer or recipient).

    Corresponds to the field TPodmiot2 from the invoice XML schema.
    """

    identification_data: Union[
        NipIdentification, EuVatIdentification, ForeignIdentification, NoIdentification
    ]
    name: Optional[str] = None
    address: Optional[Address] = None
    jst: int = 2
    gv: int = 2


# Podmiot3 role constants (TRolaPodmiotu3)
ROLE_FAKTOR = 1
ROLE_RECEIVER = 2
ROLE_ORIGINAL_ENTITY = 3
ROLE_ADDITIONAL_BUYER = 4
ROLE_INVOICE_ISSUER = 5
ROLE_PAYER = 6
ROLE_JST_ISSUER = 7
ROLE_JST_RECEIVER = 8
ROLE_VAT_GROUP_ISSUER = 9
ROLE_VAT_GROUP_RECEIVER = 10


class AdditionalRecipient(BaseModel):
    """Additional party on the invoice (Podmiot3).

    Used for e.g. a government receiver (school) when the buyer is a city hall.
    """

    identification_data: Union[
        NipIdentification, EuVatIdentification, ForeignIdentification, NoIdentification
    ]
    name: Optional[str] = None
    address: Optional[Address] = None
    role: int


class Issuer(BaseModel):
    """
    Invoice issuer.

    Corresponds to the field TPodmiot1 from the invoice XML schema.
    """

    identification_data: IssuerIdentificationData
    address: Address
    email: str
    phone: str


class InvoiceType(Enum):
    """
    Type of the invoice.

    Corresponds to the field TRodzajFaktury from the invoice XML schema.
    """

    # Regularna faktura VAT
    REGULAR_VAT = "VAT"

    # Faktura korekcyjna
    CORRECTION = "KOR"

    # Faktura zaliczkowa
    ADVANCE = "ZAL"

    # Faktura rozliczeniowa
    SETTLEMENT = "ROZ"

    # Faktura uproszczona
    SIMPLIFIED = "UPR"

    # Faktura korygująca fakturę zaliczkową
    CORRECTION_ADVANCE = "KOR_ZAL"

    # Faktura korygująca fakturę rozliczeniową
    CORRECTION_SETTLEMENT = "KOR_ROZ"


class AdditionalDescription(BaseModel):
    """Key-value note on the invoice (DodatkowyOpis / TKluczWartosc).

    Used for additional data required by law, such as exchange rate source.
    Max 256 chars each for key and value.
    """

    key: str
    value: str
    row_number: Optional[int] = None


# FormaPlatnosci enum values (TFormaPlatnosci in FA(3) schema)
PAYMENT_METHOD_CASH = 1  # gotówka
PAYMENT_METHOD_CARD = 2  # karta
PAYMENT_METHOD_VOUCHER = 3  # bon
PAYMENT_METHOD_CHECK = 4  # czek
PAYMENT_METHOD_CREDIT = 5  # kredyt
PAYMENT_METHOD_BANK_TRANSFER = 6  # przelew
PAYMENT_METHOD_MOBILE = 7  # mobilna


class PaymentInfo(BaseModel):
    """Payment information for the invoice (Platnosc element in Fa section).

    All fields are optional — include only those that apply.
    """

    is_paid: bool = False  # Zaplacono — flag "1" if fully paid
    payment_date: Optional[date] = None  # DataZaplaty — date of payment
    due_date: Optional[date] = None  # TerminPlatnosci > Termin — due date
    due_description: Optional[str] = None  # TerminPlatnosci > TerminOpis
    method: Optional[int] = None  # FormaPlatnosci — use PAYMENT_METHOD_* constants
    bank_account_number: Optional[str] = None  # RachunekBankowy > NrRB


class InvoiceData(BaseModel):
    """Invoice data.

    Corresponds to the field Fa from the invoice XML schema.
    """

    currency_code: str
    issue_date: date
    issue_number: str
    sell_date: date
    total_amount: Decimal
    tax_summary: Optional[TaxSummary] = None
    invoice_annotations: InvoiceAnnotations
    invoice_type: InvoiceType
    additional_descriptions: Sequence[AdditionalDescription] = ()
    invoice_rows: InvoiceRows
    payment_info: Optional[PaymentInfo] = None


class Invoice(BaseModel):
    """Single invoice model.

    Corresponds to the root field Faktura from the invoice XML schema.
    """

    issuer: Issuer
    recipient: Subject
    additional_recipients: Sequence[AdditionalRecipient] = ()
    invoice_data: InvoiceData
    creation_datetime: Optional[datetime] = None  # For DataWytworzeniaFa in FA(3)
