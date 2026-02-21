# 2. Authentication

The library supports two authentication methods for KSEF API v2:

- **Token Authentication** - Using a KSeF token generated via the web portal
- **XAdES Authentication** - Using a qualified certificate

Both methods follow the same flow: authenticate with KSEF, then use the resulting access token for API calls.

## Token Authentication

A KSeF token can be generated via the KSeF web portal or obtained through the API after XAdES authentication. This is the simpler method for testing.

```python
from ksef.auth.token import TokenAuthorization
from ksef.client import Client
from ksef.constants import Environment

# Create authorization instance
auth = TokenAuthorization(
    token="your-ksef-token",
    environment=Environment.TEST,
)

# Authorize with your NIP (tax identification number)
auth.authorize(nip="1234567890")

# Create client for API operations
client = Client(authorization=auth, environment=Environment.TEST)
```

!!! note "Token Format"
    KSeF tokens typically look like: `20260101-EC-XXXXXXXXXX-YYYYYYYYYY-ZZ`

## XAdES Certificate Authentication

XAdES authentication requires a qualified certificate from a trusted Certificate Authority, or a KSeF-issued certificate. You'll need both the certificate and private key in PEM format.

```python
from pathlib import Path

from ksef.auth.xades import XadesAuthorization
from ksef.client import Client
from ksef.constants import Environment

# Load certificate and key from files
cert_bytes = Path("cert.pem").read_bytes()
key_bytes = Path("key.pem").read_bytes()

# Create authorization instance
auth = XadesAuthorization(
    signing_cert=cert_bytes,
    private_key=key_bytes,
    key_password=b"optional-password",  # If your key is encrypted
    environment=Environment.TEST,
)

# Authorize with your NIP
auth.authorize(nip="1234567890")

# Create client for API operations
client = Client(authorization=auth, environment=Environment.TEST)
```

## Environments

KSEF provides three environments:

| Environment | URL | Purpose |
|-------------|-----|---------|
| `Environment.TEST` | `https://api-test.ksef.mf.gov.pl/api/v2/` | Testing and development |
| `Environment.DEMO` | `https://api-demo.ksef.mf.gov.pl/api/v2/` | Demo/sandbox environment |
| `Environment.PRODUCTION` | `https://api.ksef.mf.gov.pl/api/v2/` | Production (live invoices) |

!!! warning "Use TEST for Development"
    Always use `Environment.TEST` during development. Invoices sent to PRODUCTION are legally binding.

## Token Lifecycle

After authentication, the library manages two tokens:

- **Access Token** - Used for API calls, valid for ~15 minutes
- **Refresh Token** - Used to obtain new access tokens, valid for ~7 days

The `Client` uses the access token automatically. Token refresh is not yet implemented - for long-running operations, you may need to re-authenticate.

## Next Steps

Once authenticated, you can:

- [Send invoices](../invoices/sending-invoices.md)
- [Download invoices](../invoices/downloading-invoices.md)
