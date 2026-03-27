# Additional Recipients (Podmiot3) Reference

The `AdditionalRecipient` model represents a third party on an invoice, serialized as `Podmiot3` in the FA(3) schema. Common use cases include government receivers (a school receiving goods billed to a city hall), factoring entities, and additional buyers.

## Basic usage

```python
from ksef.models.invoice import (
    AdditionalRecipient,
    Address,
    NipIdentification,
    ROLE_RECEIVER,
)

receiver = AdditionalRecipient(
    identification_data=NipIdentification(nip="9876543210"),
    name="Szkoła Podstawowa nr 1",
    address=Address(
        country_code="PL",
        city="Tarnów",
        street="Słoneczna",
        house_number="15",
        apartment_number=None,
        postal_code="33-100",
    ),
    role=ROLE_RECEIVER,
)
```

Attach to an `Invoice`:

```python
from ksef.models.invoice import Invoice

invoice = Invoice(
    issuer=issuer,
    recipient=buyer,
    additional_recipients=[receiver],
    invoice_data=invoice_data,
)
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identification_data` | `NipIdentification \| EuVatIdentification \| ForeignIdentification \| NoIdentification` | Yes | Third party identification |
| `name` | `str` | No | Name of the third party |
| `address` | `Address` | No | Address of the third party |
| `role` | `int` | Yes | Role code (see table below) |

## Role constants

Import role constants from `ksef.models.invoice`:

```python
from ksef.models.invoice import (
    ROLE_FAKTOR,              # 1
    ROLE_RECEIVER,            # 2
    ROLE_ORIGINAL_ENTITY,     # 3
    ROLE_ADDITIONAL_BUYER,    # 4
    ROLE_INVOICE_ISSUER,      # 5
    ROLE_PAYER,               # 6
    ROLE_JST_ISSUER,          # 7
    ROLE_JST_RECEIVER,        # 8
    ROLE_VAT_GROUP_ISSUER,    # 9
    ROLE_VAT_GROUP_RECEIVER,  # 10
)
```

| Constant | Value | Description |
|----------|-------|-------------|
| `ROLE_FAKTOR` | 1 | Factoring entity |
| `ROLE_RECEIVER` | 2 | Receiver — internal unit/branch of the buyer (e.g. school under a city hall) |
| `ROLE_ORIGINAL_ENTITY` | 3 | Original entity (acquired/transformed entity) |
| `ROLE_ADDITIONAL_BUYER` | 4 | Additional buyer beyond the one in Podmiot2 |
| `ROLE_INVOICE_ISSUER` | 5 | Entity issuing the invoice on behalf of the taxpayer |
| `ROLE_PAYER` | 6 | Entity making payment on behalf of the buyer |
| `ROLE_JST_ISSUER` | 7 | Local government unit (issuer side) |
| `ROLE_JST_RECEIVER` | 8 | Local government unit (receiver side) |
| `ROLE_VAT_GROUP_ISSUER` | 9 | VAT group member (issuer) |
| `ROLE_VAT_GROUP_RECEIVER` | 10 | VAT group member (receiver) |

## Government invoice example

A typical government invoice where the buyer is a city hall (gmina) and the receiver is a school:

```python
from ksef.models.invoice import (
    AdditionalRecipient,
    Address,
    Invoice,
    NipIdentification,
    Subject,
    ROLE_RECEIVER,
)

# Buyer (Podmiot2) — city hall
buyer = Subject(
    identification_data=NipIdentification(nip="1234567890"),
    name="Urząd Miasta Tarnowa",
    address=Address(
        country_code="PL",
        city="Tarnów",
        street="Mickiewicza",
        house_number="2",
        apartment_number=None,
        postal_code="33-100",
    ),
    jst=1,  # This IS a local government unit
)

# Receiver (Podmiot3) — school
receiver = AdditionalRecipient(
    identification_data=NipIdentification(nip="9876543210"),
    name="Szkoła Podstawowa nr 1 im. Jana Kochanowskiego",
    address=Address(
        country_code="PL",
        city="Tarnów",
        street="Słoneczna",
        house_number="15",
        apartment_number=None,
        postal_code="33-100",
    ),
    role=ROLE_RECEIVER,
)

invoice = Invoice(
    issuer=issuer,
    recipient=buyer,
    additional_recipients=[receiver],
    invoice_data=invoice_data,
)
```

!!! tip "Choosing the right role"
    For government invoices where a school/hospital receives goods billed to a city hall, use `ROLE_RECEIVER` (2). This means "an internal unit/branch of the buyer that is not a separate buyer itself." Use `ROLE_JST_RECEIVER` (8) only for JST-to-JST transactions.

## Multiple additional recipients

Up to 100 `Podmiot3` elements can be added to a single invoice:

```python
invoice = Invoice(
    issuer=issuer,
    recipient=buyer,
    additional_recipients=[receiver1, receiver2, receiver3],
    invoice_data=invoice_data,
)
```

## XML output

Each `AdditionalRecipient` is serialized as a `Podmiot3` element at the root level, between `Podmiot2` and `Fa`:

```xml
<Podmiot3>
    <DaneIdentyfikacyjne>
        <NIP>9876543210</NIP>
        <Nazwa>Szkoła Podstawowa nr 1</Nazwa>
    </DaneIdentyfikacyjne>
    <Adres xsi:type="tns:TAdres">
        <KodKraju>PL</KodKraju>
        <AdresL1>Słoneczna 15</AdresL1>
        <AdresL2>33-100 Tarnów</AdresL2>
    </Adres>
    <Rola>2</Rola>
</Podmiot3>
```
