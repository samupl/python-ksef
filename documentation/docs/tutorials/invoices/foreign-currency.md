# Foreign Currency Invoices

This guide covers how to create invoices in currencies other than PLN, including exchange rate handling and PLN VAT conversion as required by Polish tax law.

## Overview

When issuing an invoice in a foreign currency (EUR, USD, etc.), Polish law (art. 106e ust. 11) requires that VAT amounts are expressed in PLN. The KSeF schema supports this through:

- **`KursWaluty`** — per-row exchange rate field in `FaWiersz`
- **`P_14_*W`** — VAT amounts converted to PLN at the summary level
- **`DodatkowyOpis`** — key-value notes for exchange rate source information

## Step 1: Set the currency

```python
from ksef.models.invoice import InvoiceData

invoice_data = InvoiceData(
    currency_code="EUR",  # ISO 4217 code
    # ...
)
```

## Step 2: Add exchange rate per row

Each invoice row can carry the exchange rate used for VAT calculation:

```python
from decimal import Decimal
from ksef.models.invoice_rows import InvoiceRow

row = InvoiceRow(
    name="Hosting service - 12 months",
    unit_of_measure="szt.",
    quantity=Decimal("1"),
    unit_net_price=Decimal("100.00"),
    net_value=Decimal("100.00"),
    tax=23,
    exchange_rate=Decimal("4.2867"),  # NBP rate, max 6 decimal places
)
```

This emits `<KursWaluty>4.2867</KursWaluty>` in the `FaWiersz` element.

!!! note "Same rate for all rows"
    When all rows use the same exchange rate (the common case), set the same `exchange_rate` on each row. For invoices with different rates per row (e.g. deliveries on different dates), set them individually — see the official KSeF example #21.

## Step 3: Provide VAT in PLN

In the `TaxSummary`, include the `*_pln` fields with VAT converted to PLN:

```python
from ksef.models.invoice import TaxSummary

rate = Decimal("4.2867")

summary = TaxSummary(
    net_standard=Decimal("100.00"),                                    # EUR
    vat_standard=Decimal("23.00"),                                     # EUR
    vat_standard_pln=(Decimal("23.00") * rate).quantize(Decimal("0.01")),  # PLN
)
```

Available PLN conversion fields:

| Field | Rate group | XML |
|-------|------------|-----|
| `vat_standard_pln` | 23%/22% | P_14_1W |
| `vat_reduced_1_pln` | 8%/7% | P_14_2W |
| `vat_reduced_2_pln` | 5% | P_14_3W |

!!! note "Not all rates have PLN fields"
    The schema only provides PLN conversion for standard, first reduced, and second reduced rates. Zero-rate, exempt, and not-subject invoices have no VAT to convert.

## Step 4: Document the exchange rate source

Polish invoices typically include the NBP exchange rate source. Use `AdditionalDescription` for this:

```python
from ksef.models.invoice import AdditionalDescription

desc = AdditionalDescription(
    key="Kurs waluty",
    value="4.2867 PLN/EUR, tabela kursów średnich NBP nr 056/A/NBP/2026 z dnia 23.03.2026",
)

invoice_data = InvoiceData(
    currency_code="EUR",
    additional_descriptions=[desc],
    # ...
)
```

This emits:

```xml
<DodatkowyOpis>
    <Klucz>Kurs waluty</Klucz>
    <Wartosc>4.2867 PLN/EUR, tabela kursów średnich NBP nr 056/A/NBP/2026 z dnia 23.03.2026</Wartosc>
</DodatkowyOpis>
```

!!! tip "Key and value limits"
    Both `Klucz` (key) and `Wartosc` (value) accept up to 256 characters each.

## Complete example

```python
from datetime import date
from decimal import Decimal

from ksef.models.invoice import (
    AdditionalDescription,
    Address,
    Invoice,
    InvoiceData,
    InvoiceType,
    Issuer,
    IssuerIdentificationData,
    NipIdentification,
    Subject,
    TaxSummary,
)
from ksef.models.invoice_rows import InvoiceRow, InvoiceRows
from ksef.models.invoice_annotations import InvoiceAnnotations

rate = Decimal("4.2867")

invoice = Invoice(
    issuer=Issuer(
        identification_data=IssuerIdentificationData(
            nip="1234567890",
            full_name="My Company Sp. z o.o.",
        ),
        address=Address(
            country_code="PL", city="Warszawa",
            street="Marszałkowska", house_number="10",
            apartment_number=None, postal_code="00-001",
        ),
        email="invoices@company.pl",
        phone="+48123456789",
    ),
    recipient=Subject(
        identification_data=NipIdentification(nip="9876543210"),
        name="Euro-Handel Sp. z o.o.",
        address=Address(
            country_code="PL", city="Kraków",
            street="Floriańska", house_number="1",
            apartment_number=None, postal_code="30-001",
        ),
    ),
    invoice_data=InvoiceData(
        currency_code="EUR",
        issue_date=date(2026, 3, 25),
        issue_number="2026/03/001",
        sell_date=date(2026, 3, 25),
        total_amount=Decimal("123.00"),
        tax_summary=TaxSummary(
            net_standard=Decimal("100.00"),
            vat_standard=Decimal("23.00"),
            vat_standard_pln=(Decimal("23.00") * rate).quantize(Decimal("0.01")),
        ),
        invoice_type=InvoiceType.REGULAR_VAT,
        additional_descriptions=[
            AdditionalDescription(
                key="Kurs waluty",
                value=f"{rate} PLN/EUR, tabela kursów średnich NBP nr 056/A/NBP/2026 z dnia 23.03.2026",
            ),
        ],
        invoice_rows=InvoiceRows(rows=[
            InvoiceRow(
                name="Hosting service",
                unit_of_measure="szt.",
                quantity=Decimal("1"),
                unit_net_price=Decimal("100.00"),
                net_value=Decimal("100.00"),
                tax=23,
                delivery_date=date(2026, 3, 25),
                exchange_rate=rate,
            ),
        ]),
        invoice_annotations=InvoiceAnnotations(),
    ),
)
```
