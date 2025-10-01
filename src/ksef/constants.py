"""Various constants used throughout the library."""

DEFAULT_HEADERS = {"Accept": "application/json"}

BASE_URL = "https://ksef-demo.mf.gov.pl/api/"  # TODO: Change to prod
TIMEOUT = 30

URL_AUTH_CHALLENGE = "auth/challenge"
URL_AUTH_INIT_TOKEN = "auth/ksef-token"  # noqa: S105
URL_AUTH_PUBLIC_KEYS = "security/public-key-certificates"

URL_QUERY_INVOICES = "invoices/query/metadata"
