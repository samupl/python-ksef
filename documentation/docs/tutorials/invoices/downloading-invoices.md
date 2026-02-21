# Downloading Invoices

This guide shows how to download invoices from KSEF.

## Prerequisites

Before downloading invoices, you must be [authenticated](../getting-started/authentication.md) with KSEF.

```python
from ksef.auth.token import TokenAuthorization
from ksef.client import Client
from ksef.constants import Environment

auth = TokenAuthorization(token="your-token", environment=Environment.TEST)
auth.authorize(nip="1234567890")
client = Client(authorization=auth, environment=Environment.TEST)
```

## Downloading by KSEF Reference Number

Once you have a KSEF reference number (assigned after invoice processing), you can download the invoice XML:

```python
# Download invoice XML
ksef_ref = "1234567890-20260101-ABCD1234EF-12"
invoice_xml = client.download_invoice(ksef_reference_number=ksef_ref)

# Save to file
with open("invoice.xml", "wb") as f:
    f.write(invoice_xml)

print(f"Downloaded {len(invoice_xml)} bytes")
```

The returned content is the original FA(3) XML invoice as stored in KSEF.

## Parsing Downloaded XML

You can parse the downloaded XML using standard Python libraries:

```python
from lxml import etree

# Parse the XML
root = etree.fromstring(invoice_xml)

# Define namespace
ns = {"fa": "http://crd.gov.pl/wzor/2025/06/25/13775/"}

# Extract data
issue_number = root.find(".//fa:P_2", ns).text
issue_date = root.find(".//fa:P_1", ns).text

print(f"Invoice: {issue_number} dated {issue_date}")
```

## Error Handling

Handle cases where the invoice doesn't exist or isn't accessible:

```python
from requests.exceptions import HTTPError

try:
    invoice_xml = client.download_invoice(ksef_reference_number=ksef_ref)
except HTTPError as e:
    if e.response.status_code == 404:
        print("Invoice not found")
    elif e.response.status_code == 403:
        print("Access denied - not authorized to view this invoice")
    else:
        print(f"Error: {e.response.status_code}")
```

## KSEF Reference Number Format

KSEF reference numbers follow a specific format and are assigned by KSEF after successful invoice processing. They look like:

```
1234567890-20260101-ABCD1234EF-12
```

!!! note "Reference vs Submission Number"
    Don't confuse the **KSEF reference number** (assigned after processing) with the **submission reference number** (returned immediately when you submit). The download endpoint requires the KSEF reference number.

## Next Steps

- See the [Invoice Models Reference](../../reference/invoice-models.md) for data structures
- See the [Invoice Annotations Reference](../../reference/invoice-annotations.md) for annotation details
