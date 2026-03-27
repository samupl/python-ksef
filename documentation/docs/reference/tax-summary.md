# Tax Summary Reference

The `TaxSummary` model provides net and VAT totals grouped by tax rate at the invoice level. These correspond to the `P_13_*` (net) and `P_14_*` (VAT) fields in the KSeF FA(3) schema.

!!! note "Why is this needed?"
    KSeF displays Netto and VAT columns on the invoice list based on these summary fields — not from individual row amounts. Without a `TaxSummary`, KSeF shows 0,00 for both Netto and VAT.

## Basic usage

```python
from decimal import Decimal
from ksef.models.invoice import TaxSummary

# Invoice with items at 23% VAT
summary = TaxSummary(
    net_standard=Decimal("1000.00"),   # P_13_1
    vat_standard=Decimal("230.00"),    # P_14_1
)
```

Attach it to `InvoiceData`:

```python
from ksef.models.invoice import InvoiceData

invoice_data = InvoiceData(
    # ...
    total_amount=Decimal("1230.00"),
    tax_summary=summary,
    # ...
)
```

## Fields for rates with VAT

These fields come in pairs — net amount + VAT amount. Both must be set together.

| Net field | VAT field | PLN field | Rate group | XML |
|-----------|-----------|-----------|------------|-----|
| `net_standard` | `vat_standard` | `vat_standard_pln` | 23% or 22% | P_13_1 / P_14_1 / P_14_1W |
| `net_reduced_1` | `vat_reduced_1` | `vat_reduced_1_pln` | 8% or 7% | P_13_2 / P_14_2 / P_14_2W |
| `net_reduced_2` | `vat_reduced_2` | `vat_reduced_2_pln` | 5% | P_13_3 / P_14_3 / P_14_3W |
| `net_flat_rate` | `vat_flat_rate` | — | 4% or 3% | P_13_4 / P_14_4 |
| `net_oss` | `vat_oss` | — | OSS/IOSS | P_13_5 / P_14_5 |

!!! tip "Shared rate groups"
    23% and 22% both go into `net_standard`/`vat_standard`. Similarly 8%/7% share `net_reduced_1`, and 4%/3% share `net_flat_rate`. If an invoice has items at both 23% and 22%, sum them together.

## Fields for zero-rate and special rates (net only)

These rates have no VAT, so only a net amount field exists:

| Field | Rate | XML |
|-------|------|-----|
| `net_zero_domestic` | 0% domestic (0 KR) | P_13_6_1 |
| `net_zero_wdt` | 0% intra-Community (0 WDT) | P_13_6_2 |
| `net_zero_export` | 0% export (0 EX) | P_13_6_3 |
| `net_exempt` | Exempt (zw) | P_13_7 |
| `net_not_subject` | Not subject (np I) | P_13_8 |
| `net_not_subject_art100` | Not subject art. 100 (np II) | P_13_9 |
| `net_reverse_charge` | Reverse charge (oo) | P_13_10 |

## Foreign currency invoices (PLN conversion)

When the invoice is in a foreign currency (EUR, USD, etc.), Polish law requires VAT to be expressed in PLN. Use the `*_pln` fields:

```python
summary = TaxSummary(
    net_standard=Decimal("100.00"),         # Net in EUR
    vat_standard=Decimal("23.00"),          # VAT in EUR
    vat_standard_pln=Decimal("98.31"),      # P_14_1W — VAT converted to PLN
)
```

The PLN amount is calculated as `vat_amount * exchange_rate`. Only `P_14_1W`, `P_14_2W`, and `P_14_3W` exist in the schema — there are no PLN conversion fields for flat-rate or OSS.

## Example: mixed rates

```python
summary = TaxSummary(
    # Items at 23%
    net_standard=Decimal("500.00"),
    vat_standard=Decimal("115.00"),
    # Items at 8%
    net_reduced_1=Decimal("200.00"),
    vat_reduced_1=Decimal("16.00"),
    # Items at 0% WDT
    net_zero_wdt=Decimal("300.00"),
)
```

## XML element ordering

Tax summary fields are emitted **before** `P_15` (gross total) in the `Fa` section:

```xml
<Fa>
    <KodWaluty>PLN</KodWaluty>
    <P_1>2026-03-25</P_1>
    <P_2>FV/2026/03/001</P_2>
    <P_6>2026-03-25</P_6>
    <!-- Tax summary here -->
    <P_13_1>500.00</P_13_1>
    <P_14_1>115.00</P_14_1>
    <P_13_2>200.00</P_13_2>
    <P_14_2>16.00</P_14_2>
    <P_13_6_2>300.00</P_13_6_2>
    <!-- Then gross total -->
    <P_15>1131.00</P_15>
    <Adnotacje>...</Adnotacje>
    ...
</Fa>
```
