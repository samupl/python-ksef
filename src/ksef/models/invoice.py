"""Invoice model."""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from ksef.models.invoice_annotations import InvoiceAnnotations
from ksef.models.invoice_rows import InvoiceRows


class IssuerIdentificationData(BaseModel):
    """
    Subject identification data.

    Corresponds to the field TPodmiot1/TPodmiot2 from the invoice XML schema.
    """

    nip: str
    full_name: str


class SubjectIdentificationData(BaseModel):
    """
    Subject identification data.

    Corresponds to the field TPodmiot1/TPodmiot2 from the invoice XML schema.
    """

    nip: str


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

    identification_data: SubjectIdentificationData


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
