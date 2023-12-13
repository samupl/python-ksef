"""Various constants used throughout the library."""

DEFAULT_HEADERS = {"Accept": "application/json"}

BASE_URL = "https://ksef-demo.mf.gov.pl/api/"  # TODO: Change to prod
TIMEOUT = 30

URL_AUTH_CHALLENGE = "online/Session/AuthorisationChallenge"
URL_AUTH_INIT_TOKEN = "online/Session/InitToken"  # noqa: S105

URL_QUERY_INVOICES = "online/Query/Invoice/Sync"
