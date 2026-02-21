# Invoice Models Reference

This reference documents all models used to create invoices.

## Invoice

The root invoice model.

```python
from ksef.models.invoice import Invoice

invoice = Invoice(
    issuer=...,           # Issuer - seller information
    recipient=...,        # Subject - buyer information
    invoice_data=...,     # InvoiceData - invoice details
    creation_datetime=..., # Optional[datetime] - for FA(3) schema
)
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issuer` | `Issuer` | Yes | Seller/issuer information |
| `recipient` | `Subject` | Yes | Buyer/recipient information |
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

Information about the invoice recipient (buyer).

```python
from ksef.models.invoice import Subject, SubjectIdentificationData, Address

recipient = Subject(
    identification_data=SubjectIdentificationData(
        nip="0987654321",
    ),
    # Optional: buyer address
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
| `identification_data` | `SubjectIdentificationData` | Yes | Recipient NIP |
| `address` | `Address` | No | Buyer address (maps to `Adres` in `Podmiot2`) |
| `jst` | `int` | No | Is the buyer a local government unit? `1` = yes, `2` = no (default: `2`) |
| `gv` | `int` | No | Is the buyer a government entity? `1` = yes, `2` = no (default: `2`) |

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
from ksef.models.invoice import InvoiceData, InvoiceType
from ksef.models.invoice_rows import InvoiceRows, InvoiceRow
from ksef.models.invoice_annotations import InvoiceAnnotations, ...

invoice_data = InvoiceData(
    currency_code="PLN",
    issue_date=date.today(),
    issue_number="FV/2026/001",
    sell_date=date.today(),
    total_amount=Decimal("1230.00"),
    invoice_type=InvoiceType.REGULAR_VAT,
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
| `total_amount` | `Decimal` | Yes | Total invoice amount |
| `invoice_type` | `InvoiceType` | Yes | Type of invoice |
| `invoice_rows` | `InvoiceRows` | Yes | Line items |
| `invoice_annotations` | `InvoiceAnnotations` | Yes | Required annotations |

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

Single line item on an invoice.

```python
from ksef.models.invoice_rows import InvoiceRow

row = InvoiceRow(
    name="Consulting services",
    tax=23,  # VAT rate in percent
)
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Name/description of item or service |
| `tax` | `int` | Yes | VAT rate (e.g., 23, 8, 5, 0) |

---

## InvoiceRows

Container for invoice line items.

```python
from ksef.models.invoice_rows import InvoiceRows, InvoiceRow

rows = InvoiceRows(rows=[
    InvoiceRow(name="Service A", tax=23),
    InvoiceRow(name="Service B", tax=23),
])
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rows` | `Sequence[InvoiceRow]` | Yes | List of line items |
