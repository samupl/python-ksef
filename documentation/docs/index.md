# Python-KSEF Documentation

A Python library for the Polish KSEF (National e-Invoice System, Krajowy System e-Faktur).

!!! warning "Early Development"
    This library is in early alpha development. The API may change between versions.

## Features

- **Token Authentication** - Authenticate using KSeF tokens
- **XAdES Authentication** - Authenticate using qualified certificates
- **Send Invoices** - Submit invoices to KSEF with encryption
- **Check Invoice Status** - Verify if invoices were accepted or rejected
- **Download Invoices** - Retrieve invoice XML by KSEF reference number
- **FA(3) Schema** - Full support for the latest invoice schema

## Quick Start

### Installation

```bash
pip install ksef
```

Or with uv:

```bash
uv add ksef
```

### Send an Invoice

```python
from datetime import date, datetime, timezone
from decimal import Decimal

from ksef.auth.token import TokenAuthorization
from ksef.client import Client
from ksef.constants import Environment
from ksef.models.invoice import (
    Address, Invoice, InvoiceData, InvoiceType,
    Issuer, IssuerIdentificationData, Subject, NipIdentification,
)
from ksef.models.invoice_annotations import (
    InvoiceAnnotations, TaxSettlementOnPayment, SelfInvoicing,
    ReverseCharge, SplitPayment, FreeFromVat,
    IntraCommunitySupplyOfNewTransportMethods,
    SimplifiedProcedureBySecondTaxPayer, MarginProcedure,
)
from ksef.models.invoice_rows import InvoiceRow, InvoiceRows

# Authenticate
auth = TokenAuthorization(token="your-token", environment=Environment.TEST)
auth.authorize(nip="1234567890")
client = Client(authorization=auth, environment=Environment.TEST)

# Create invoice
invoice = Invoice(
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
            apartment_number=None,
            postal_code="00-001",
        ),
        email="contact@example.com",
        phone="+48 123456789",
    ),
    recipient=Subject(
        identification_data=NipIdentification(nip="0987654321"),
    ),
    invoice_data=InvoiceData(
        currency_code="PLN",
        issue_date=date.today(),
        issue_number="FV/2026/001",
        sell_date=date.today(),
        total_amount=Decimal("1230.00"),
        invoice_type=InvoiceType.REGULAR_VAT,
        invoice_rows=InvoiceRows(rows=[
            InvoiceRow(name="Consulting services", tax=23),
        ]),
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
    creation_datetime=datetime.now(tz=timezone.utc),
)

# Send invoice
response = client.send_invoice(nip="1234567890", invoice=invoice)
print(f"Submitted! Reference: {response.reference_number}")

# Check invoice status
status = client.get_invoice_status(
    session_reference_number=response.session_reference_number,
    invoice_reference_number=response.reference_number,
)
if status.status.code == 200:
    print(f"Invoice accepted! KSeF number: {status.ksef_number}")
else:
    print(f"Invoice rejected ({status.status.code}): {status.status.description}")
    if status.status.details:
        for detail in status.status.details:
            print(f"  - {detail}")
```

## Documentation

- **[Installation](tutorials/getting-started/installation.md)** - How to install the library
- **[Authentication](tutorials/getting-started/authentication.md)** - Token and XAdES authentication
- **[Sending Invoices](tutorials/invoices/sending-invoices.md)** - Submit invoices to KSEF
- **[Downloading Invoices](tutorials/invoices/downloading-invoices.md)** - Retrieve invoices from KSEF
- **[Invoice Models](reference/invoice-models.md)** - Reference for invoice data structures
- **[Invoice Annotations](reference/invoice-annotations.md)** - Reference for required annotations

## Environments

| Environment | URL | Purpose |
|-------------|-----|---------|
| `Environment.TEST` | `api-test.ksef.mf.gov.pl` | Testing and development |
| `Environment.DEMO` | `api-demo.ksef.mf.gov.pl` | Demo/sandbox |
| `Environment.PRODUCTION` | `api.ksef.mf.gov.pl` | Production (live invoices) |

## Links

- [Official KSEF API Documentation](https://github.com/CIRFMF/ksef-docs)
- [GitHub Repository](https://github.com/samupl/python-ksef)
