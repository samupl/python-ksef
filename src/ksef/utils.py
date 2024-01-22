"""Miscellaneous utilities."""

import re
from http import HTTPStatus
from typing import Optional

from requests import Response

from ksef.exceptions import KsefError, RateLimitExceededError, UnsupportedResponseError

_CAMELCASE_TO_UNDERSCORE_RE = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")
_HTTP_STATUS_RANGE_START = 200
_HTTP_STATUS_RANGE_END = 299


def camelcase_to_words(value: str) -> str:
    """
    Convert a CamelCase string to a readable "Camel case" string.

    Remove the camel case, capitalize the first letter.

    :param value: Value to convert
    """
    new_value = _CAMELCASE_TO_UNDERSCORE_RE.sub(r" \1", value).lower()
    return new_value[0].upper() + new_value[1:]


def response_to_exception(response: Response) -> Optional[KsefError]:
    """Convert a requests.Response object to a KsefError exception instance."""
    if _HTTP_STATUS_RANGE_START <= response.status_code <= _HTTP_STATUS_RANGE_END:
        return None

    if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        return RateLimitExceededError(response=response)

    return UnsupportedResponseError(response=response)
