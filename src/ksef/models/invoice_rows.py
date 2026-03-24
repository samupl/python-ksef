"""Models for individual invoice rows/positions."""

from decimal import Decimal
from typing import Literal, Optional, Sequence

from pydantic import BaseModel

# KSeF tax rate constants for the P_12 field (TStawkaPodatku in FA(3) schema)
TAX_23 = 23
TAX_22 = 22
TAX_8 = 8
TAX_7 = 7
TAX_5 = 5
TAX_4 = 4
TAX_3 = 3
TAX_0_KR = "0 KR"  # 0% domestic
TAX_0_WDT = "0 WDT"  # 0% intra-Community supply
TAX_0_EX = "0 EX"  # 0% export of goods
TAX_ZW = "zw"  # exempt from tax
TAX_OO = "oo"  # reverse charge
TAX_NP_I = "np I"  # not subject to taxation — supply outside country territory
TAX_NP_II = "np II"  # not subject to taxation — services per art. 100(1)(4)

TaxRate = Literal[
    23,
    22,
    8,
    7,
    5,
    4,
    3,
    "0 KR",
    "0 WDT",
    "0 EX",
    "zw",
    "oo",
    "np I",
    "np II",
]

# Set of valid P_12 integer rates for quick lookup
VALID_P12_RATES = {23, 22, 8, 7, 5, 4, 3}


class InvoiceRow(BaseModel):
    """Single individual invoice position."""

    name: str  # P_7, nazwa (rodzaj) towaru lub usługi
    tax: Optional[TaxRate] = None  # P_12, standard tax rate
    tax_oss: Optional[Decimal] = None  # P_12_XII, OSS/IOSS procedure tax rate (arbitrary %)


class InvoiceRows(BaseModel):
    """Group of invoice positions."""

    rows: Sequence[InvoiceRow]
