"""Invoice model."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Union

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
    invoice_rows: InvoiceRows


class Invoice(BaseModel):
    """Single invoice model.

    Corresponds to the root field Faktura from the invoice XML schema.
    """

    issuer: Issuer
    recipient: Subject
    invoice_data: InvoiceData
    creation_datetime: Optional[datetime] = None  # For DataWytworzeniaFa in FA(3)
