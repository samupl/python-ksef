# Invoice Models Reference

This reference documents all models used to create invoices.

## Invoice

The root invoice model.

```python
from ksef.models.invoice import Invoice

invoice = Invoice(
    issuer=...,                  # Issuer - seller information
    recipient=...,               # Subject - buyer information
    additional_recipients=[...], # Optional - Podmiot3 entries
    invoice_data=...,            # InvoiceData - invoice details
    creation_datetime=...,       # Optional[datetime] - for FA(3) schema
)
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issuer` | `Issuer` | Yes | Seller/issuer information |
| `recipient` | `Subject` | Yes | Buyer/recipient information |
| `additional_recipients` | `Sequence[AdditionalRecipient]` | No | Third parties ([Podmiot3](additional-recipients.md)) |
| `invoice_data` | `InvoiceData` | Yes | Invoice details and line items |
| `creation_datetime` | `datetime` | No | Invoice creation timestamp (recommended) |

---

## Issuer

Information about the invoice issuer (seller).

```python
from ksef.models.invoice import Issuer, IssuerIdentificationData, Address

issuer = Issuer(
    identification_data=IssuerIdentificationData(
        nip="1234567890",
        full_name="Company Name Sp. z o.o.",
    ),
    address=Address(
        country_code="PL",
        city="Warszawa",
        street="Street Name",
        house_number="1",
        apartment_number="2A",  # Optional
        postal_code="00-001",
    ),
    email="contact@company.com",
    phone="+48 123456789",
)
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identification_data` | `IssuerIdentificationData` | Yes | NIP and company name |
| `address` | `Address` | Yes | Company address |
| `email` | `str` | Yes | Contact email |
| `phone` | `str` | Yes | Contact phone |

---

## Subject (Recipient)

Information about the invoice recipient (buyer). The `identification_data` field accepts four identification types matching the FA(3) schema's `DaneIdentyfikacyjne` choices for `Podmiot2`.

### Identification types

**Polish company (NIP)**

```python
from ksef.models.invoice import Subject, NipIdentification

recipient = Subject(
    identification_data=NipIdentification(nip="0987654321"),
)
```

> `SubjectIdentificationData` is a backwards-compatible alias for `NipIdentification`.

**EU company (VAT)**

```python
from ksef.models.invoice import Subject, EuVatIdentification

recipient = Subject(
    identification_data=EuVatIdentification(eu_country_code="DE", eu_vat_number="123456789"),
    name="Deutsche Firma GmbH",
)
```

**Non-EU entity**

```python
from ksef.models.invoice import Subject, ForeignIdentification

recipient = Subject(
    identification_data=ForeignIdentification(country_code="US", tax_id="EIN123456"),
    name="American Corp.",
)
```

**Individual / no tax ID (B2C)**

```python
from ksef.models.invoice import Subject, NoIdentification

recipient = Subject(
    identification_data=NoIdentification(),
    name="Jan Kowalski",
)
```

### Full example with address

```python
from ksef.models.invoice import Subject, NipIdentification, Address

recipient = Subject(
    identification_data=NipIdentification(nip="0987654321"),
    name="Firma Testowa Sp. z o.o.",
    address=Address(
        country_code="PL",
        city="Kraków",
        street="Rynek Główny",
        house_number="1",
        apartment_number=None,
        postal_code="30-001",
    ),
    jst=2,  # 1 = local government unit, 2 = no (default)
    gv=2,   # 1 = government entity, 2 = no (default)
)
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identification_data` | `NipIdentification \| EuVatIdentification \| ForeignIdentification \| NoIdentification` | Yes | Buyer identification (see types below) |
| `name` | `str` | No | Buyer name (maps to `Nazwa` in `Podmiot2`) |
| `address` | `Address` | No | Buyer address (maps to `Adres` in `Podmiot2`) |
| `jst` | `int` | No | Is the buyer a local government unit? `1` = yes, `2` = no (default: `2`) |
| `gv` | `int` | No | Is the buyer a government entity? `1` = yes, `2` = no (default: `2`) |

### Identification type fields

| Type | Fields | XML output |
|------|--------|------------|
| `NipIdentification` | `nip: str` | `<NIP>` |
| `EuVatIdentification` | `eu_country_code: str`, `eu_vat_number: str` | `<KodUE>` + `<NrVatUE>` |
| `ForeignIdentification` | `country_code: Optional[str]`, `tax_id: str` | `<KodKraju>` (optional) + `<NrID>` |
| `NoIdentification` | *(none)* | `<BrakID>1</BrakID>` |

---

## Address

Address data. Used for both the issuer (`Podmiot1`) and optionally the recipient (`Podmiot2`).

In the FA(3) schema, address fields are mapped to a flat format: `AdresL1` (street + house/apartment number) and `AdresL2` (postal code + city).

```python
from ksef.models.invoice import Address

address = Address(
    country_code="PL",
    city="Warszawa",
    street="Przykładowa",
    house_number="1",
    apartment_number="2A",
    postal_code="00-001",
)
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `country_code` | `str` | Yes | ISO country code (e.g., "PL") |
| `city` | `str` | Yes | City name |
| `street` | `str` | Yes | Street name |
| `house_number` | `str` | Yes | Building number |
| `apartment_number` | `str` | No | Apartment/unit number |
| `postal_code` | `str` | Yes | Postal code |

---

## InvoiceData

Main invoice data including line items and annotations.

```python
from datetime import date
from decimal import Decimal
from ksef.models.invoice import InvoiceData, InvoiceType, TaxSummary, AdditionalDescription
from ksef.models.invoice_rows import InvoiceRows, InvoiceRow
from ksef.models.invoice_annotations import InvoiceAnnotations, ...

invoice_data = InvoiceData(
    currency_code="PLN",
    issue_date=date.today(),
    issue_number="FV/2026/001",
    sell_date=date.today(),
    total_amount=Decimal("1230.00"),
    tax_summary=TaxSummary(...),
    invoice_type=InvoiceType.REGULAR_VAT,
    additional_descriptions=[AdditionalDescription(...)],
    invoice_rows=InvoiceRows(rows=[...]),
    invoice_annotations=InvoiceAnnotations(...),
)
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `currency_code` | `str` | Yes | ISO currency code (e.g., "PLN", "EUR") |
| `issue_date` | `date` | Yes | Invoice issue date |
| `issue_number` | `str` | Yes | Invoice number (e.g., "FV/2026/001") |
| `sell_date` | `date` | Yes | Date of sale/service |
| `total_amount` | `Decimal` | Yes | Total gross amount (P_15) |
| `tax_summary` | [`TaxSummary`](tax-summary.md) | No | Net/VAT totals per rate (P_13/P_14) |
| `invoice_type` | `InvoiceType` | Yes | Type of invoice |
| `additional_descriptions` | `Sequence[AdditionalDescription]` | No | Key-value notes (DodatkowyOpis) |
| `invoice_rows` | `InvoiceRows` | Yes | Line items |
| `invoice_annotations` | `InvoiceAnnotations` | Yes | Required annotations |

!!! note "AdditionalDescription"
    Key-value pairs for additional data on the invoice. Common use: exchange rate source info for foreign currency invoices. See the [Foreign Currency](../tutorials/invoices/foreign-currency.md) guide.

    | Field | Type | Required | Description |
    |-------|------|----------|-------------|
    | `key` | `str` | Yes | Label (max 256 chars) |
    | `value` | `str` | Yes | Value (max 256 chars) |
    | `row_number` | `int` | No | Ties the note to a specific row |

---

## InvoiceType

Enum for invoice types.

```python
from ksef.models.invoice import InvoiceType

# Regular VAT invoice
invoice_type = InvoiceType.REGULAR_VAT
```

| Value | Description |
|-------|-------------|
| `REGULAR_VAT` | Standard VAT invoice |
| `CORRECTION` | Correction invoice (faktura korygująca) |
| `ADVANCE` | Advance payment invoice (faktura zaliczkowa) |
| `SETTLEMENT` | Settlement invoice (faktura rozliczeniowa) |
| `SIMPLIFIED` | Simplified invoice (faktura uproszczona) |
| `CORRECTION_ADVANCE` | Correction of advance invoice |
| `CORRECTION_SETTLEMENT` | Correction of settlement invoice |

---

## InvoiceRow

Single line item on an invoice. Only `name` is required — all other fields are optional but recommended for complete invoices.

```python
from datetime import date
from decimal import Decimal
from ksef.models.invoice_rows import InvoiceRow, TAX_23

row = InvoiceRow(
    name="Hosting service - 12 months",
    unit_of_measure="szt.",
    quantity=Decimal("1"),
    unit_net_price=Decimal("100.00"),
    net_value=Decimal("100.00"),
    tax=TAX_23,
    delivery_date=date(2026, 3, 25),
    exchange_rate=Decimal("4.2867"),  # Foreign currency only
)
```

| Field | Type | Required | Description | XML |
|-------|------|----------|-------------|-----|
| `name` | `str` | Yes | Product/service name | P_7 |
| `unit_of_measure` | `str` | No | Unit (e.g. "szt.", "kg") | P_8A |
| `quantity` | `Decimal` | No | Quantity | P_8B |
| `unit_net_price` | `Decimal` | No | Net price per unit | P_9A |
| `net_value` | `Decimal` | No | Total net value for the row | P_11 |
| `tax` | [`TaxRate`](tax-rates.md) | No | Standard tax rate | P_12 |
| `tax_oss` | `Decimal` | No | OSS/IOSS tax rate (%) | P_12_XII |
| `delivery_date` | `date` | No | Delivery/service date | P_6A |
| `exchange_rate` | `Decimal` | No | Exchange rate (max 6 decimals) | KursWaluty |

!!! tip "tax vs tax_oss"
    Set exactly one of `tax` or `tax_oss` per row. Use `tax` for rates in the [standard KSeF enum](tax-rates.md). Use `tax_oss` for arbitrary OSS/IOSS percentage rates. See the [Tax Rates](tax-rates.md) reference for details.

---

## InvoiceRows

Container for invoice line items.

```python
from ksef.models.invoice_rows import InvoiceRows, InvoiceRow, TAX_23

rows = InvoiceRows(rows=[
    InvoiceRow(name="Service A", tax=TAX_23, net_value=Decimal("100.00")),
    InvoiceRow(name="Service B", tax=TAX_23, net_value=Decimal("200.00")),
])
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rows` | `Sequence[InvoiceRow]` | Yes | List of line items |
