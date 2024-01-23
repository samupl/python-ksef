"""Models for individual invoice rows/positions."""

from typing import Sequence

from pydantic import BaseModel


class InvoiceRow(BaseModel):
    """Single individual invoice position."""

    name: str  # P_7, nazwa (rodzaj) towaru lub usługi
    tax: int  # P_12, stawka podatku


class InvoiceRows(BaseModel):
    """Group of invoice positions."""

    rows: Sequence[InvoiceRow]
