"""Various constants used throughout the library."""

from enum import Enum


class Environment(Enum):
    """KSEF API environment."""

    PRODUCTION = "https://api.ksef.mf.gov.pl/api/v2/"
    DEMO = "https://api-demo.ksef.mf.gov.pl/api/v2/"
    TEST = "https://api-test.ksef.mf.gov.pl/api/v2/"


DEFAULT_HEADERS = {"Accept": "application/json"}

TIMEOUT = 30

URL_AUTH_CHALLENGE = "auth/challenge"
URL_AUTH_KSEF_TOKEN = "auth/ksef-token"  # noqa: S105
URL_AUTH_XADES_SIGNATURE = "auth/xades-signature"
URL_AUTH_STATUS = "auth/{reference_number}"
URL_AUTH_TOKEN_REDEEM = "auth/token/redeem"  # noqa: S105
URL_AUTH_TOKEN_REFRESH = "auth/token/refresh"  # noqa: S105
URL_PUBLIC_KEY_CERTS = "security/public-key-certificates"

URL_QUERY_INVOICES = "invoices/query/metadata"
