"""Base client for interacting with the KSEF API."""
from typing import Dict, Mapping, Optional, Union, cast
from urllib.parse import urlencode, urljoin

import requests
from requests import Request

from ksef.auth.base import Authorization
from ksef.constants import BASE_URL, URL_QUERY_INVOICES


class Client:
    """Base client for interacting with the KSEF API."""

    def __init__(self, authorization: Authorization, base_url: str = BASE_URL):
        self.authorization = authorization
        self.base_url = base_url
        self.session = requests.Session()

    def build_url(self, url: str, params: Optional[Mapping[str, Union[str, int]]] = None) -> str:
        """Construct a full URL."""
        url = urljoin(base=self.base_url, url=url)
        if params is not None:
            param_str = urlencode(params)
            return f"{url}?{param_str}"

        return url

    def search_invoices(self, page_size: int = 100, page_offset: int = 0) -> Dict[str, str]:
        """Search for invoices with the specified page size and offset."""
        params = {
            "PageSize": page_size,
            "PageOffset": page_offset,
        }
        request = Request(
            method="POST",
            url=self.build_url(url=URL_QUERY_INVOICES, params=params),
            json={
                "queryCriteria": {
                    "subjectType": "subject1",
                    "type": "range",
                    "invoicingDateFrom": "2023-11-14T13:21:09.000Z",
                    "invoicingDateTo": "2023-12-12T13:21:09.000Z",
                }
            },
        )
        request = self.authorization.modify_request(request)
        prepared_request = request.prepare()
        response = self.session.send(prepared_request)
        data = cast(Dict[str, str], response.json())
        return data
