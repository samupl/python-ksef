"""Models for invoice annotations/metadata."""
from enum import Enum

from pydantic import BaseModel


class ReverseCharge(Enum):
    """Possible values for the reverse charge field."""

    YES = "1"
    NO = "2"


class TaxSettlementOnPayment(Enum):
    """Possible values for the tax settlement on payment field."""

    ON_PAYMENT = "1"
    REGULAR = "2"


class SelfInvoicing(Enum):
    """Possible values for the self invoicing field."""

    YES = "1"
    NO = "2"


class SplitPayment(Enum):
    """Possible values for the split payment field."""

    YES = "1"
    NO = "2"


class FreeFromVat(Enum):
    """Possible values for the free from vat tax field."""

    YES = "1"
    NO = "2"


class IntraCommunitySupplyOfNewTransportMethods(Enum):
    """Possible values for the intra community supply of new transport methods field."""

    YES = "1"
    NO = "2"


class SimplifiedProcedureBySecondTaxPayer(Enum):
    """Possible values of the simplified procedure by second tax payer field."""

    YES = "1"
    NO = "2"


class MarginProcedure(Enum):
    """Possible values for the margin procedure field."""

    YES = "1"
    NO = "2"


class InvoiceAnnotations(BaseModel):
    """Invoice annotations/metadata."""

    # P_16, Metoda kasowa
    tax_settlement_on_payment: TaxSettlementOnPayment

    # P_17, Samofakturowanie
    self_invoice: SelfInvoicing

    # P_18, Odwrotne obciążenie
    reverse_charge: ReverseCharge

    # P_18A, Mechanizm podzielonej płatności
    split_payment: SplitPayment

    # P_19, Zwolnienie z VAT
    free_from_vat: FreeFromVat

    # P_22, Wewnątrzwspólnotowa dostawa nowych środków transportu
    intra_community_supply_of_new_transport_methods: IntraCommunitySupplyOfNewTransportMethods

    # P_23, faktura wystawiona uproszczoną procedurą przez drugiego w kolejności podatnika
    simplified_procedure_by_second_tax_payer: SimplifiedProcedureBySecondTaxPayer

    # P_PMarzy, znacznik wystąpienia procedur marży
    margin_procedure: MarginProcedure
