"""Base client for interacting with the KSEF API."""
import logging
from typing import Dict, Mapping, Optional, Union, cast
from urllib.parse import urlencode, urljoin

import requests

from ksef.auth.base import Authorization
from ksef.constants import URL_QUERY_INVOICES, Environment

logger = logging.getLogger(__name__)


class Client:
    """Base client for interacting with the KSEF API."""

    def __init__(
        self,
        authorization: Authorization,
        environment: Environment = Environment.PRODUCTION,
    ):
        self.authorization = authorization
        self.base_url = environment.value
        self.session = requests.Session()

    def build_url(self, url: str, params: Optional[Mapping[str, Union[str, int]]] = None) -> str:
        """Construct a full URL."""
        url = urljoin(base=self.base_url, url=url)
        if params is not None:
            param_str = urlencode(params)
            return f"{url}?{param_str}"

        return url

    def _auth_headers(self) -> Dict[str, str]:
        """Build authorization headers using the Bearer access token."""
        return {"Authorization": f"Bearer {self.authorization.get_access_token()}"}

    def search_invoices(self, page_size: int = 100, page_offset: int = 0) -> Dict[str, str]:
        """Search for invoices with the specified page size and offset."""
        params = {
            "PageSize": page_size,
            "PageOffset": page_offset,
        }
        response = self.session.post(
            url=self.build_url(url=URL_QUERY_INVOICES, params=params),
            headers={
                "Accept": "application/json",
                **self._auth_headers(),
            },
            json={
                "queryCriteria": {
                    "subjectType": "subject1",
                    "type": "range",
                    "invoicingDateFrom": "2023-11-14T13:21:09.000Z",
                    "invoicingDateTo": "2023-12-12T13:21:09.000Z",
                }
            },
        )
        logger.debug("Search invoices response (%s): %s", response.status_code, response.text)
        response.raise_for_status()
        data = cast(Dict[str, str], response.json())
        return data
