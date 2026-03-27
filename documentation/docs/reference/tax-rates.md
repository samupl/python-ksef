# Tax Rates Reference

The KSeF FA(3) schema defines a fixed set of valid tax rates for the `P_12` field on invoice rows. The library provides type-safe constants and a `TaxRate` literal type to prevent invalid values.

## TaxRate type

```python
from ksef.models.invoice_rows import TaxRate
```

`TaxRate` is a `Literal` type that accepts only valid KSeF `TStawkaPodatku` values. Using any other value will cause a Pydantic validation error.

## Standard rates

Integer percentage rates for domestic Polish VAT:

```python
from ksef.models.invoice_rows import (
    TAX_23,  # 23% — standard rate
    TAX_22,  # 22% — previous standard rate
    TAX_8,   # 8% — first reduced rate
    TAX_7,   # 7% — previous first reduced rate
    TAX_5,   # 5% — second reduced rate
    TAX_4,   # 4% — flat-rate for personal taxis
    TAX_3,   # 3% — previous taxi flat-rate
)
```

Usage:

```python
from ksef.models.invoice_rows import InvoiceRow, TAX_23

row = InvoiceRow(name="Hosting service", tax=TAX_23)
```

## Zero rates

Three distinct 0% rates, each with different legal meaning:

```python
from ksef.models.invoice_rows import (
    TAX_0_KR,   # "0 KR"  — 0% domestic (sprzedaż krajowa)
    TAX_0_WDT,  # "0 WDT" — 0% intra-Community supply of goods
    TAX_0_EX,   # "0 EX"  — 0% export of goods
)
```

!!! note "There is no plain `0` rate"
    KSeF requires zero-rate invoices to specify which type of zero rate applies. Use `TAX_0_KR` for domestic, `TAX_0_WDT` for intra-Community, or `TAX_0_EX` for exports.

## Special rates

String-based rates for special tax treatment:

```python
from ksef.models.invoice_rows import (
    TAX_ZW,     # "zw"    — exempt from tax (zwolnione od podatku)
    TAX_OO,     # "oo"    — reverse charge (odwrotne obciążenie)
    TAX_NP_I,   # "np I"  — not subject to taxation (supply outside country territory)
    TAX_NP_II,  # "np II" — not subject to taxation (services per art. 100(1)(4))
)
```

## OSS/IOSS rates (P_12_XII)

For EU consumer sales under the One Stop Shop procedure, the VAT rate of the customer's country may not be in the standard KSeF enum (e.g. 21% for Belgium, 19% for Germany). Use `tax_oss` instead of `tax`:

```python
from decimal import Decimal
from ksef.models.invoice_rows import InvoiceRow

# Belgian consumer — 21% VAT via OSS
row = InvoiceRow(
    name="Digital service",
    tax_oss=Decimal("21"),  # Goes into P_12_XII, not P_12
)
```

!!! tip "When to use `tax` vs `tax_oss`"
    - Use `tax` for rates in the standard KSeF enum (23, 22, 8, 7, 5, 4, 3, and the string constants).
    - Use `tax_oss` for arbitrary percentage rates under OSS/IOSS that are not in the enum.
    - Only set one of `tax` or `tax_oss` per row, never both.

## Complete reference table

| Constant | Value | XML field | Description |
|----------|-------|-----------|-------------|
| `TAX_23` | `23` | P_12 | Standard rate (23%) |
| `TAX_22` | `22` | P_12 | Previous standard rate (22%) |
| `TAX_8` | `8` | P_12 | First reduced rate (8%) |
| `TAX_7` | `7` | P_12 | Previous first reduced rate (7%) |
| `TAX_5` | `5` | P_12 | Second reduced rate (5%) |
| `TAX_4` | `4` | P_12 | Taxi flat-rate (4%) |
| `TAX_3` | `3` | P_12 | Previous taxi flat-rate (3%) |
| `TAX_0_KR` | `"0 KR"` | P_12 | 0% domestic |
| `TAX_0_WDT` | `"0 WDT"` | P_12 | 0% intra-Community supply |
| `TAX_0_EX` | `"0 EX"` | P_12 | 0% export |
| `TAX_ZW` | `"zw"` | P_12 | Exempt from tax |
| `TAX_OO` | `"oo"` | P_12 | Reverse charge |
| `TAX_NP_I` | `"np I"` | P_12 | Not subject to taxation |
| `TAX_NP_II` | `"np II"` | P_12 | Not subject (art. 100) |
| *(decimal)* | e.g. `21` | P_12_XII | OSS/IOSS rate |
