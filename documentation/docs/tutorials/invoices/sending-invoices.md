# Sending Invoices

This guide shows how to send invoices to KSEF using the library.

## Prerequisites

Before sending invoices, you must be [authenticated](../getting-started/authentication.md) with KSEF.

```python
from ksef.auth.token import TokenAuthorization
from ksef.client import Client
from ksef.constants import Environment

auth = TokenAuthorization(token="your-token", environment=Environment.TEST)
auth.authorize(nip="1234567890")
client = Client(authorization=auth, environment=Environment.TEST)
```

## Creating an Invoice

First, create an `Invoice` object with all required data:

```python
from datetime import date, datetime, timezone
from decimal import Decimal

from ksef.models.invoice import (
    Address,
    Invoice,
    InvoiceData,
    InvoiceType,
    Issuer,
    IssuerIdentificationData,
    Subject,
    NipIdentification,
)
from ksef.models.invoice_annotations import (
    FreeFromVat,
    IntraCommunitySupplyOfNewTransportMethods,
    InvoiceAnnotations,
    MarginProcedure,
    ReverseCharge,
    SelfInvoicing,
    SimplifiedProcedureBySecondTaxPayer,
    SplitPayment,
    TaxSettlementOnPayment,
)
from ksef.models.invoice_rows import InvoiceRow, InvoiceRows

invoice = Invoice(
    # Issuer (seller) information
    issuer=Issuer(
        identification_data=IssuerIdentificationData(
            nip="1234567890",
            full_name="My Company Sp. z o.o.",
        ),
        address=Address(
            country_code="PL",
            city="Warszawa",
            street="Przykładowa",
            house_number="1",
            apartment_number="2A",
            postal_code="00-001",
        ),
        email="contact@example.com",
        phone="+48 123456789",
    ),

    # Recipient (buyer) information
    # Use NipIdentification for Polish companies, or one of:
    # - EuVatIdentification(eu_country_code="DE", eu_vat_number="123456789") for EU
    # - ForeignIdentification(country_code="US", tax_id="EIN123") for non-EU
    # - NoIdentification() for individuals (B2C)
    recipient=Subject(
        identification_data=NipIdentification(
            nip="0987654321",
        ),
        # name="Buyer Name Sp. z o.o.",  # Optional buyer name
        # Optional: buyer address
        address=Address(
            country_code="PL",
            city="Kraków",
            street="Rynek Główny",
            house_number="1",
            apartment_number=None,
            postal_code="30-001",
        ),
        # jst=2,  # 1 = local government unit, 2 = no (default)
        # gv=2,   # 1 = government entity, 2 = no (default)
    ),

    # Invoice details
    invoice_data=InvoiceData(
        currency_code="PLN",
        issue_date=date.today(),
        issue_number="FV/2026/001",
        sell_date=date.today(),
        total_amount=Decimal("1230.00"),
        invoice_type=InvoiceType.REGULAR_VAT,

        # Invoice line items
        invoice_rows=InvoiceRows(rows=[
            InvoiceRow(name="Consulting services", tax=23),
            InvoiceRow(name="Software license", tax=23),
        ]),

        # Required annotations (usually all NO for standard invoices)
        invoice_annotations=InvoiceAnnotations(
            tax_settlement_on_payment=TaxSettlementOnPayment.REGULAR,
            self_invoice=SelfInvoicing.NO,
            reverse_charge=ReverseCharge.NO,
            split_payment=SplitPayment.NO,
            free_from_vat=FreeFromVat.NO,
            intra_community_supply_of_new_transport_methods=IntraCommunitySupplyOfNewTransportMethods.NO,
            simplified_procedure_by_second_tax_payer=SimplifiedProcedureBySecondTaxPayer.NO,
            margin_procedure=MarginProcedure.NO,
        ),
    ),

    # Creation timestamp (required for FA(3) schema)
    creation_datetime=datetime.now(tz=timezone.utc),
)
```

## Recipient Types

The `Subject` model supports four identification types for the buyer, matching the FA(3) schema:

```python
from ksef.models.invoice import (
    Subject, NipIdentification, EuVatIdentification,
    ForeignIdentification, NoIdentification,
)

# Polish company (B2B)
recipient = Subject(identification_data=NipIdentification(nip="0987654321"))

# EU company
recipient = Subject(
    identification_data=EuVatIdentification(eu_country_code="DE", eu_vat_number="123456789"),
    name="Deutsche Firma GmbH",
)

# Non-EU entity
recipient = Subject(
    identification_data=ForeignIdentification(country_code="US", tax_id="EIN123456"),
    name="American Corp.",
)

# Individual / no tax ID (B2C)
recipient = Subject(
    identification_data=NoIdentification(),
    name="Jan Kowalski",
)
```

See the [Invoice Models Reference](../../reference/invoice-models.md#subject-recipient) for full details on each type.

## Sending with the Convenience Method

The simplest way to send an invoice is using the `send_invoice()` method, which handles the entire session lifecycle automatically:

```python
response = client.send_invoice(nip="1234567890", invoice=invoice)

print(f"Invoice submitted! Reference: {response.reference_number}")
```

This method:

1. Opens an encrypted session with KSEF
2. Encrypts and sends your invoice
3. Closes the session
4. Returns the submission reference number

!!! note "Asynchronous Processing"
    KSEF processes invoices asynchronously. The `reference_number` returned is for tracking - the actual KSEF invoice number (`ksef_reference_number`) is assigned after processing completes.

## Sending Multiple Invoices (Session-Based)

For sending multiple invoices efficiently, use the session-based approach:

```python
# Open a session
session_context = client.open_session(nip="1234567890")

try:
    # Send multiple invoices in the same session
    for invoice in invoices:
        response = client.send_invoice_in_session(
            session_context=session_context,
            invoice=invoice,
        )
        print(f"Submitted: {response.reference_number}")

finally:
    # Always close the session
    client.close_session(session_context)
```

!!! tip "Session Benefits"
    Using a single session for multiple invoices is more efficient because:

    - Encryption keys are generated only once
    - Fewer API round-trips
    - Better performance for batch operations

## Invoice Types

The library supports all KSEF invoice types:

| Type | Enum Value | Description |
|------|------------|-------------|
| Regular VAT | `InvoiceType.REGULAR_VAT` | Standard VAT invoice |
| Correction | `InvoiceType.CORRECTION` | Correction invoice |
| Advance | `InvoiceType.ADVANCE` | Advance payment invoice |
| Settlement | `InvoiceType.SETTLEMENT` | Settlement invoice |
| Simplified | `InvoiceType.SIMPLIFIED` | Simplified invoice |
| Correction Advance | `InvoiceType.CORRECTION_ADVANCE` | Correction of advance invoice |
| Correction Settlement | `InvoiceType.CORRECTION_SETTLEMENT` | Correction of settlement invoice |

## Error Handling

Handle potential errors during invoice submission:

```python
from requests.exceptions import HTTPError

try:
    response = client.send_invoice(nip="1234567890", invoice=invoice)
    print(f"Success: {response.reference_number}")
except HTTPError as e:
    print(f"KSEF API error: {e.response.status_code}")
    print(f"Details: {e.response.text}")
except Exception as e:
    print(f"Error: {e}")
```

## Checking Invoice Status

KSEF processes invoices asynchronously. After submitting, use `get_invoice_status()` to check whether the invoice was accepted or rejected:

```python
import time

response = client.send_invoice(nip="1234567890", invoice=invoice)

# Poll until processing completes
for attempt in range(10):
    time.sleep(2)
    status = client.get_invoice_status(
        session_reference_number=response.session_reference_number,
        invoice_reference_number=response.reference_number,
    )

    if status.status.code == 200:
        print(f"Invoice accepted! KSeF number: {status.ksef_number}")
        break

    if status.status.code >= 400:
        print(f"Rejected ({status.status.code}): {status.status.description}")
        if status.status.details:
            for detail in status.status.details:
                print(f"  - {detail}")
        break

    print(f"Still processing (attempt {attempt + 1})...")
```

You can also check the overall session status:

```python
session_status = client.get_session_status(
    session_reference_number=response.session_reference_number,
)
print(f"Total: {session_status.invoice_count}")
print(f"Accepted: {session_status.successful_invoice_count}")
print(f"Rejected: {session_status.failed_invoice_count}")
```

## Next Steps

- [Download invoices](downloading-invoices.md) to retrieve invoice XML
- Learn about [invoice annotations](../../reference/invoice-annotations.md) for special cases
